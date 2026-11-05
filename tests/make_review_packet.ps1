# Builds a review packet for an independent reviewer (ChatGPT / Antigravity).
#
#   powershell -ExecutionPolicy Bypass -File tests\make_review_packet.ps1 -From v2.0.0-baseline
#
# Writes scratch\reviews\<tag-or-range>\ containing:
#   change.diff      full source diff (excluding binaries)
#   files.txt        changed files with add/remove counts
#   api.diff         only the changed function and class signatures
#   summary.txt      git revision, hashes, test verdicts, ZIP sha
#   zip-sha.txt      sha256 of giggle_addon.zip and of the zip's __init__.py entry
#
# The diff is the evidence; the summary is only an index into it.

param(
    [string]$From = 'v2.0.0-baseline',
    [string]$To = 'HEAD',
    [string]$Label = ''
)

$root = Split-Path -Parent $PSScriptRoot
if (-not $Label) {
    $Label = ("{0}..{1}" -f ($From -replace '[^\w\.\-]', '_'), ($To -replace '[^\w\.\-]', '_'))
}
$out = Join-Path $root "scratch\reviews\$Label"
New-Item -ItemType Directory -Force -Path $out | Out-Null

$rev = git -C $root rev-parse --short $To
$base = git -C $root rev-parse --short $From
git -C $root diff --no-color $From $To -- . ':(exclude)*.zip' ':(exclude)*.blend' ':(exclude)*.blend1' |
    Set-Content -Path (Join-Path $out 'change.diff') -Encoding utf8
git -C $root diff --no-color --numstat $From $To -- . ':(exclude)*.zip' ':(exclude)*.blend' |
    Set-Content -Path (Join-Path $out 'files.txt') -Encoding utf8
git -C $root diff --no-color -U0 $From $To -- 'giggle_addon/__init__.py' |
    Select-String -Pattern '^[+-]\s*(def |class )' |
    ForEach-Object { $_.Line } |
    Set-Content -Path (Join-Path $out 'api.diff') -Encoding utf8

$zip = Join-Path $root 'giggle_addon.zip'
$zipHash = if (Test-Path $zip) { (Get-FileHash $zip).Hash } else { 'missing' }
Add-Type -AssemblyName System.IO.Compression.FileSystem
if (Test-Path $zip) {
    $archive = [System.IO.Compression.ZipFile]::OpenRead($zip)
    $entry = $archive.Entries | Where-Object { $_.FullName -eq 'giggle_addon/__init__.py' }
    $ms = New-Object System.IO.MemoryStream
    $entry.Open().CopyTo($ms)
    $entryHash = ([BitConverter]::ToString(
            [System.Security.Cryptography.SHA256]::Create().ComputeHash($ms.ToArray())) -replace '-', '')
    $archive.Dispose()
}

$lines = @(
    "Giggle review packet $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "range      : $From ($base) .. $To ($rev)",
    "source sha : $((Get-FileHash (Join-Path $root 'giggle_addon\__init__.py')).Hash)",
    "zip sha    : $zipHash",
    "zip entry  : giggle_addon/__init__.py $entryHash",
    "",
    "Changed files (numstat):"
)
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
$lines | Set-Content -Path (Join-Path $out 'summary.txt') -Encoding utf8

Write-Host "review packet: $out"
$lines | ForEach-Object { Write-Host $_ }
