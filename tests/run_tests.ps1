# Runs the Giggle regression tests on every installed Blender version.
#
#   powershell -ExecutionPolicy Bypass -File tests\run_tests.ps1
#
# Both suites are headless. Before each run the source is copied into that Blender's installed
# extension, so the acceptance suite cannot test a stale install. Every run is teed into
# artifacts\<timestamp>\ for handoff, together with summary.txt (git revision, file hashes,
# Blender versions and the PASS/FAIL lines).

param(
    [string]$Blend = (Join-Path (Split-Path -Parent $PSScriptRoot) 'poc_cage_xpbd_kasumi.blend'),
    [string[]]$Blender = @(
        'D:\blender-5.3.0-beta+v53.a6f145b151fa-windows.amd64-release\blender.exe',
        'D:\Blender 5.2\blender.exe'
    ),
    [string]$Artifacts = (Join-Path (Split-Path -Parent $PSScriptRoot) 'artifacts')
)

$root = Split-Path -Parent $PSScriptRoot
$out = Join-Path $Artifacts (Get-Date -Format 'yyyyMMdd_HHmmss')
New-Item -ItemType Directory -Force -Path $out | Out-Null

$source = Join-Path $root 'giggle_addon\__init__.py'
$sourceHash = (Get-FileHash $source).Hash
$summary = New-Object System.Collections.Generic.List[string]
$summary.Add("Giggle test run $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$summary.Add("blend      : $Blend")
$summary.Add("source sha : $sourceHash")
if (Test-Path (Join-Path $root '.git')) {
    $rev = (git -C $root rev-parse --short HEAD) 2>$null
    $branch = (git -C $root rev-parse --abbrev-ref HEAD) 2>$null
    $dirty = ((git -C $root status --porcelain) | Measure-Object).Count -gt 0
    $summary.Add("git        : $branch @ $rev$(if ($dirty) { ' (dirty working tree)' })")
}

$failed = 0
$ran = 0

foreach ($exe in $Blender) {
    if (-not (Test-Path $exe)) {
        Write-Host "SKIP (not installed): $exe"
        $summary.Add("SKIP  $exe (not installed)")
        continue
    }
    $product = (Get-Item $exe).VersionInfo.ProductVersion
    $label = if ($product -match '^(\d+\.\d+)') { $matches[1] } else { 'unknown' }

    # Keep the installed extension equal to the source under test.
    $install = Join-Path $env:APPDATA "Blender Foundation\Blender\$label\extensions\user_default\giggle_physics"
    if (Test-Path $install) {
        Copy-Item $source (Join-Path $install '__init__.py') -Force
        $changelog = Join-Path $root 'giggle_addon\CHANGELOG.md'
        if (Test-Path $changelog) { Copy-Item $changelog (Join-Path $install 'CHANGELOG.md') -Force }
        $installedHash = (Get-FileHash (Join-Path $install '__init__.py')).Hash
        $match = $installedHash -eq $sourceHash
        Write-Host "installed $label synced: $match"
        $summary.Add("run   Blender $label ($product): installed copy matches source = $match")
        if (-not $match) { $failed++ }
    } else {
        Write-Host "WARNING: giggle_physics is not installed for Blender $label; the acceptance suite will fail"
        $summary.Add("run   Blender $label ($product): extension NOT installed at $install")
    }

    foreach ($suite in @(
            @{ Key = 'maintenance'; Name = 'maintenance phase 1'; Path = (Join-Path $PSScriptRoot 'test_maintenance_phase1.py') },
            @{ Key = 'acceptance'; Name = 'milestone 3 acceptance'; Path = (Join-Path $root 'scratch\test_milestone3_acceptance.py') }
        )) {
        if (-not (Test-Path $suite.Path)) {
            $summary.Add("FAIL  $($suite.Name) on $label : script missing ($($suite.Path))")
            $failed++
            continue
        }
        $log = Join-Path $out ("{0}_{1}.log" -f $label, $suite.Key)
        Write-Host "=== Blender $label : $($suite.Name) ==="
        & $exe -b $Blend --python-exit-code 1 --python $suite.Path *> $log
        $code = $LASTEXITCODE
        $ran++
        $verdict = if ($code -eq 0) { 'PASS' } else { 'FAIL' }
        if ($code -ne 0) { $failed++ }
        $checks = (Select-String -Path $log -Pattern '^RESULT ' | Select-Object -Last 1).Line
        $summary.Add(("{0}  {1,-24} Blender {2} (exit {3}){4}" -f $verdict, $suite.Name, $label, $code,
                $(if ($checks) { " - $checks" } else { '' })))
        Get-Content $log | Select-String -Pattern '^(PASS|FAIL|SKIP)|ALL MILESTONE|AssertionError' |
            ForEach-Object { Write-Host $_.Line }
    }
}

$summary.Add("")
$summary.Add($(if ($failed -gt 0) { "RESULT: $failed failure(s)" } else { "RESULT: all $ran suite run(s) passed" }))
$summary.Add("logs: $out")
$summary | Set-Content -Path (Join-Path $out 'summary.txt') -Encoding utf8
$summary | ForEach-Object { Write-Host $_ }

if ($failed -gt 0) { exit 1 }
exit 0
