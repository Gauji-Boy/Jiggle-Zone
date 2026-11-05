# Builds a review packet for an independent reviewer (ChatGPT / Antigravity).
#
#   powershell -ExecutionPolicy Bypass -File tests\make_review_packet.ps1 -From v2.0.0-baseline
#
# Writes scratch\reviews\<label>\ containing:
#   change.diff      committed source diff (binaries excluded)
#   files.txt        changed files with add/remove counts
#   api.diff         only the changed function and class signatures
#   summary.txt      git revision, status, hashes, test verdicts
#   zip-sha.txt      sha256 of giggle_addon.zip and of every entry it contains
#
# The diff is the evidence; the summary is only an index into it.
#
# The packet is only trustworthy if the ZIP was built from the commit it describes, so this
# refuses a dirty working tree (override with -AllowDirty, which is recorded in the summary),
# records `git status --short`, and fails when the ZIP's contents differ from the tree.
#
# Line endings: the repository stores LF and checks out CRLF on Windows (core.autocrlf=true),
# so the working file and the committed blob hash differently while being the same content.
# The summary therefore reports the working-file hash (what the ZIP holds) and proves it equals
# the committed blob by comparing both after normalising CRLF to LF.

param(
    [string]$From = 'v2.0.0-baseline',
    [string]$To = 'HEAD',
    [string]$Label = '',
    [switch]$AllowDirty
)

$root = Split-Path -Parent $PSScriptRoot
if (-not $Label) {
    $Label = ("{0}..{1}" -f ($From -replace '[^\w\.\-]', '_'), ($To -replace '[^\w\.\-]', '_'))
}
$out = Join-Path $root "scratch\reviews\$Label"
$problems = New-Object System.Collections.Generic.List[string]

function Fail([string]$Message) {
    $problems.Add($Message)
    Write-Host "FAIL $Message"
}

function Get-Sha256([string]$Path) {
    return (Get-FileHash -Algorithm SHA256 -Path $Path).Hash
}

function Get-NormalisedBytesHash([byte[]]$Bytes) {
    # SHA-256 with CRLF collapsed to LF, i.e. what git stores.
    $stream = New-Object System.IO.MemoryStream
    for ($i = 0; $i -lt $Bytes.Length; $i++) {
        if ($Bytes[$i] -eq 13 -and ($i + 1) -lt $Bytes.Length -and $Bytes[$i + 1] -eq 10) { continue }
        $stream.WriteByte($Bytes[$i])
    }
    $hash = [System.Security.Cryptography.SHA256]::Create().ComputeHash($stream.ToArray())
    $stream.Dispose()
    return ([BitConverter]::ToString($hash) -replace '-', '')
}

function Get-NormalisedHash([string]$Path) {
    return (Get-NormalisedBytesHash ([System.IO.File]::ReadAllBytes($Path)))
}

# 1. Working tree state. A packet taken over uncommitted edits cannot be checked against the diff.
$statusLines = @(git -C $root status --short)
$dirty = $statusLines.Count -gt 0
if ($dirty -and -not $AllowDirty) {
    Fail "working tree is dirty ($($statusLines.Count) path(s)); commit first or pass -AllowDirty"
    $statusLines | ForEach-Object { Write-Host "     $_" }
}
$diffAgainstTarget = @(git -C $root diff --name-only $To -- .)
if ($diffAgainstTarget.Count -gt 0) {
    Fail "$To does not match the working tree; the ZIP would not be described by change.diff"
    $diffAgainstTarget | ForEach-Object { Write-Host "     $_" }
}

New-Item -ItemType Directory -Force -Path $out | Out-Null

$rev = (git -C $root rev-parse --short "${To}^{commit}")
$base = (git -C $root rev-parse --short "${From}^{commit}")
$branch = (git -C $root rev-parse --abbrev-ref HEAD)

# 2. The diff itself, always from commits.
git -C $root diff --no-color $From $To -- . ':(exclude)*.zip' ':(exclude)*.blend' ':(exclude)*.blend1' |
    Set-Content -Path (Join-Path $out 'change.diff') -Encoding utf8
git -C $root diff --no-color --numstat $From $To -- . ':(exclude)*.zip' ':(exclude)*.blend' |
    Set-Content -Path (Join-Path $out 'files.txt') -Encoding utf8
git -C $root diff --no-color -U0 $From $To -- 'giggle_addon/__init__.py' |
    Select-String -Pattern '^[+-]\s*(def |class )' |
    ForEach-Object { $_.Line } |
    Set-Content -Path (Join-Path $out 'api.diff') -Encoding utf8

# 3. The source the ZIP must contain, checked three ways.
$sourcePath = Join-Path $root 'giggle_addon\__init__.py'
$sourceHash = Get-Sha256 $sourcePath
$sourceNormalised = Get-NormalisedHash $sourcePath

$blobFile = Join-Path ([System.IO.Path]::GetTempPath()) ("giggle_blob_{0}.py" -f [guid]::NewGuid().ToString('N'))
try {
    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = 'git'
    $startInfo.Arguments = "-C `"$root`" show `"${To}:giggle_addon/__init__.py`""
    $startInfo.RedirectStandardOutput = $true
    $startInfo.UseShellExecute = $false
    $process = [System.Diagnostics.Process]::Start($startInfo)
    $blobStream = New-Object System.IO.MemoryStream
    $process.StandardOutput.BaseStream.CopyTo($blobStream)
    $process.WaitForExit()
    [System.IO.File]::WriteAllBytes($blobFile, $blobStream.ToArray())
    $blobStream.Dispose()
    if ($process.ExitCode -ne 0) { throw "git show exited $($process.ExitCode)" }
} catch {
    Fail "could not read the committed blob for ${To}:giggle_addon/__init__.py ($_)"
}
if (-not (Test-Path $blobFile)) {
    $blobHash = 'missing'
    $blobSize = 0
    $blobMatchesTree = $false
} else {
    $blobHash = Get-Sha256 $blobFile
    $blobSize = (Get-Item $blobFile).Length
    $blobMatchesTree = ((Get-NormalisedHash $blobFile) -eq $sourceNormalised)
    if (-not $blobMatchesTree) {
        Fail "the committed blob and the working file differ beyond line endings"
    }
}

$zip = Join-Path $root 'giggle_addon.zip'
if (-not (Test-Path $zip)) {
    Fail "giggle_addon.zip is missing; run tests\repack_zip.py"
    $zipHash = 'missing'
    $entryHash = 'missing'
    $zipEntries = @()
} else {
    $zipHash = Get-Sha256 $zip
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [System.IO.Compression.ZipFile]::OpenRead($zip)
    $zipEntries = New-Object System.Collections.Generic.List[string]
    $entryHash = ''
    foreach ($entry in $archive.Entries) {
        $stream = New-Object System.IO.MemoryStream
        $entry.Open().CopyTo($stream)
        $bytes = $stream.ToArray()
        $stream.Dispose()
        $hash = ([BitConverter]::ToString(
                [System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)) -replace '-', '')
        $zipEntries.Add(("{0} {1}" -f $hash, $entry.FullName))
        if ($entry.FullName -eq 'giggle_addon/__init__.py') { $entryHash = $hash }

        $relative = $entry.FullName -replace '^giggle_addon/', ''
        $onDisk = Join-Path (Join-Path $root 'giggle_addon') ($relative -replace '/', '\')
        if (-not (Test-Path $onDisk)) {
            Fail "zip entry $($entry.FullName) has no file in the source tree"
        } elseif ((Get-NormalisedHash $onDisk) -ne (Get-NormalisedBytesHash $bytes)) {
            # The repository stores LF and checks out CRLF, so an entry can hold either form of
            # the same content. Compare the content, not the line endings.
            Fail "zip entry $($entry.FullName) differs from the source tree beyond line endings; rebuild the ZIP"
        }
    }
    $archive.Dispose()

    if ($entryHash -ne $sourceHash) {
        Fail "the ZIP's __init__.py is not the working file; rebuild the ZIP"
    }
}
$zipEntries | Set-Content -Path (Join-Path $out 'zip-sha.txt') -Encoding utf8

$lines = @(
    "Giggle review packet $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "range      : $From ($base) .. $To ($rev)",
    "branch     : $branch",
    "working tree: $(if ($dirty) { "DIRTY ($($statusLines.Count) path(s))$(if ($AllowDirty) { ' - allowed' } else { '' })" } else { 'clean' })",
    "source sha : $sourceHash  (giggle_addon/__init__.py, working copy)",
    "blob sha   : $blobHash  (${To}:giggle_addon/__init__.py as stored, $blobSize bytes)",
    "blob == tree (CRLF collapsed): $blobMatchesTree",
    "zip sha    : $zipHash",
    "zip entry  : giggle_addon/__init__.py $entryHash",
    "zip == tree: every entry checked against the source tree above",
    "",
    "git status --short:"
)
if ($statusLines.Count -eq 0) {
    $lines += "  (nothing to report)"
} else {
    $lines += ($statusLines | ForEach-Object { "  $_" })
}
$lines += ""
$lines += "Changed files (numstat):"
$lines += (Get-Content (Join-Path $out 'files.txt'))
$latestRun = Get-ChildItem (Join-Path $root 'artifacts') -Directory -ErrorAction SilentlyContinue |
    Sort-Object Name | Select-Object -Last 1
if ($latestRun) {
    $lines += ""
    $lines += "Latest test run ($($latestRun.Name)):"
    $lines += (Get-Content (Join-Path $latestRun.FullName 'summary.txt'))
} else {
    $lines += ""
    $lines += "No test run found; run tests\run_tests.ps1 first."
}
$lines += ""
if ($problems.Count -gt 0) {
    $lines += "PACKET PROBLEMS ($($problems.Count)):"
    $lines += ($problems | ForEach-Object { "  $_" })
} else {
    $lines += "PACKET PROBLEMS: none"
}
$lines | Set-Content -Path (Join-Path $out 'summary.txt') -Encoding utf8

if (Test-Path $blobFile) { Remove-Item $blobFile -Force }

Write-Host "review packet: $out"
$lines | ForEach-Object { Write-Host $_ }

if ($problems.Count -gt 0) { exit 1 }
exit 0
