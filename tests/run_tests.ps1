# Runs the Jiggle regression tests on every installed Blender version.
#
#   powershell -ExecutionPolicy Bypass -File tests\run_tests.ps1
#
# Every suite is headless. Before each run the source and its assets are copied into that
# Blender's installed extension, so the suites cannot test a stale install. Suites with no
# blend file run under --factory-startup. The source-level name audit is plain Python and runs
# once, since it reads the tree rather than a Blender session. Every run is teed into
# artifacts\<timestamp>\ for handoff, together with summary.txt (git revision, file hashes,
# Blender versions and the PASS/FAIL lines).

param(
    [string]$Blend = (Join-Path (Split-Path -Parent $PSScriptRoot) 'poc_cage_xpbd_kasumi.blend'),
    [string]$SecondaryBlend = (Join-Path (Split-Path -Parent $PSScriptRoot) 'JitterArmatureModel.blend'),
    [string[]]$Blender = @(
        'D:\Blender 5.3\blender.exe',
        'D:\Blender 5.2\blender.exe'
    ),
    [string]$Artifacts = (Join-Path (Split-Path -Parent $PSScriptRoot) 'artifacts')
)

$root = Split-Path -Parent $PSScriptRoot
$out = Join-Path $Artifacts (Get-Date -Format 'yyyyMMdd_HHmmss')
New-Item -ItemType Directory -Force -Path $out | Out-Null

$source = Join-Path $root 'jiggle_zone\__init__.py'
$sourceHash = (Get-FileHash $source).Hash
$summary = New-Object System.Collections.Generic.List[string]
$summary.Add("Jiggle test run $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
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
    $install = Join-Path $env:APPDATA "Blender Foundation\Blender\$label\extensions\user_default\jiggle_zone"
    if (Test-Path $install) {
        Copy-Item $source (Join-Path $install '__init__.py') -Force
        $changelog = Join-Path $root 'jiggle_zone\CHANGELOG.md'
        if (Test-Path $changelog) { Copy-Item $changelog (Join-Path $install 'CHANGELOG.md') -Force }
        # The node groups live in assets\; without them add_zone cannot create a zone.
        $assets = Join-Path $root 'jiggle_zone\assets'
        if (Test-Path $assets) {
            $target = Join-Path $install 'assets'
            New-Item -ItemType Directory -Force -Path $target | Out-Null
            Copy-Item (Join-Path $assets '*.blend') $target -Force
        }
        $installedHash = (Get-FileHash (Join-Path $install '__init__.py')).Hash
        $match = $installedHash -eq $sourceHash
        Write-Host "installed $label synced: $match"
        $summary.Add("run   Blender $label ($product): installed copy matches source = $match")
        if (-not $match) { $failed++ }
    } else {
        Write-Host "WARNING: jiggle_zone is not installed for Blender $label; the acceptance suite will fail"
        $summary.Add("run   Blender $label ($product): extension NOT installed at $install")
    }

    # scratch\test_milestone3_acceptance.py is deliberately absent: it targets the 2.x add-on
    # (import giggle_addon, bl_info, bpy.ops.giggle.*), none of which survived the 3.0 rename.
    # Its intent (operators registered, cache validity, rebake) is covered by the maintenance,
    # secondary-scene and viewport suites below.
    foreach ($suite in @(
            @{ Key = 'maintenance'; Name = 'maintenance phase 1'; Path = (Join-Path $PSScriptRoot 'test_maintenance_phase1.py'); Blend = $Blend },
            @{ Key = 'viewport'; Name = 'runtime viewport QA'; Path = (Join-Path $PSScriptRoot 'runtime\test_viewport_qa.py'); Blend = $Blend },
            @{ Key = 'secondary'; Name = 'secondary scene smoke'; Path = (Join-Path $PSScriptRoot 'runtime\test_secondary_scene.py'); Blend = $SecondaryBlend },
            @{ Key = 'install'; Name = 'clean install from zip'; Path = (Join-Path $PSScriptRoot 'runtime\test_clean_install_zip.py'); Blend = $null },
            @{ Key = 'legacy_names'; Name = 'legacy 2.x names'; Path = (Join-Path $PSScriptRoot 'runtime\test_legacy_names.py'); Blend = $null },
            @{ Key = 'wiggy_versions'; Name = 'wiggy 0.1 + 0.2.0'; Path = (Join-Path $PSScriptRoot 'runtime\test_wiggy_versions.py'); Blend = $null },
            @{ Key = 'legacy_attach'; Name = 'legacy clothing attach'; Path = (Join-Path $PSScriptRoot 'runtime\test_legacy_attach.py'); Blend = $Blend },
            @{ Key = 'cage_rebuild'; Name = 'cage rebuild clothing'; Path = (Join-Path $PSScriptRoot 'runtime\test_cage_rebuild_preserves_clothing.py'); Blend = $Blend }
        )) {
        if (-not (Test-Path $suite.Path)) {
            $summary.Add("FAIL  $($suite.Name) on $label : script missing ($($suite.Path))")
            $failed++
            continue
        }
        if ($suite.Blend -and -not (Test-Path $suite.Blend)) {
            $summary.Add("SKIP  $($suite.Name) on $label : blend missing ($($suite.Blend))")
            continue
        }
        $log = Join-Path $out ("{0}_{1}.log" -f $label, $suite.Key)
        Write-Host "=== Blender $label : $($suite.Name) ==="
        if ($suite.Blend) {
            & $exe -b $suite.Blend --python-exit-code 1 --python $suite.Path *> $log
        } else {
            & $exe -b --factory-startup --python-exit-code 1 --python $suite.Path *> $log
        }
        $code = $LASTEXITCODE
        $ran++
        $verdict = if ($code -eq 0) { 'PASS' } else { 'FAIL' }
        if ($code -ne 0) { $failed++ }
        $checks = (Select-String -Path $log -Pattern '^RESULT ' | Select-Object -Last 1).Line
        $summary.Add(("{0}  {1,-24} Blender {2} (exit {3}){4}" -f $verdict, $suite.Name, $label, $code,
                $(if ($checks) { " - $checks" } else { '' })))
        Get-Content $log | Select-String -Pattern '^(PASS|FAIL|SKIP|NOT TESTED)|ALL MILESTONE|AssertionError' |
            ForEach-Object { Write-Host $_.Line }
    }
}

# The name audit needs no Blender: it reads jiggle_zone\ and fails if a hardcoded Wiggy group
# name reappears outside the compatibility definition and the asset map. --selftest proves the
# audit still detects a regression, so a broken audit cannot quietly pass every future run.
$python = (Get-Command python -ErrorAction SilentlyContinue).Source
foreach ($audit in @(
        @{ Key = 'name_audit'; Name = 'wiggy name audit'; Args = @() },
        @{ Key = 'name_audit_selftest'; Name = 'wiggy audit selftest'; Args = @('--selftest') }
    )) {
    $script = Join-Path $PSScriptRoot 'test_wiggy_name_audit.py'
    if (-not (Test-Path $script)) {
        $summary.Add("FAIL  $($audit.Name) : script missing ($script)")
        $failed++
        continue
    }
    if (-not $python) {
        $summary.Add("FAIL  $($audit.Name) : Python is required but not on PATH")
        $failed++
        continue
    }
    $log = Join-Path $out ("python_{0}.log" -f $audit.Key)
    Write-Host "=== python : $($audit.Name) ==="
    & $python $script @($audit.Args) *> $log
    $code = $LASTEXITCODE
    $ran++
    $verdict = if ($code -eq 0) { 'PASS' } else { 'FAIL' }
    if ($code -ne 0) { $failed++ }
    $checks = (Select-String -Path $log -Pattern '^RESULT |^PASS selftest' | Select-Object -Last 1).Line
    $summary.Add(("{0}  {1,-24} python (exit {2}){3}" -f $verdict, $audit.Name, $code,
            $(if ($checks) { " - $checks" } else { '' })))
    Get-Content $log | Select-String -Pattern '^(PASS|FAIL) ' | ForEach-Object { Write-Host $_.Line }
}

$summary.Add("")
$summary.Add($(if ($failed -gt 0) { "RESULT: $failed failure(s)" } else { "RESULT: all $ran suite run(s) passed" }))
$summary.Add("logs: $out")
$summary | Set-Content -Path (Join-Path $out 'summary.txt') -Encoding utf8
$summary | ForEach-Object { Write-Host $_ }

if ($failed -gt 0) { exit 1 }
exit 0
