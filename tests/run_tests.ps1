# Runs the Giggle regression tests on every installed Blender version.
#
#   powershell -ExecutionPolicy Bypass -File tests\run_tests.ps1
#
# Both suites are headless. The acceptance suite needs the add-on installed in each Blender
# (extensions\user_default\giggle_physics); the maintenance suite loads the source directly.

param(
    [string]$Blend = (Join-Path (Split-Path -Parent $PSScriptRoot) 'poc_cage_xpbd_kasumi.blend'),
    [string[]]$Blender = @(
        'D:\blender-5.3.0-beta+v53.a6f145b151fa-windows.amd64-release\blender.exe',
        'D:\Blender 5.2\blender.exe'
    )
)

$root = Split-Path -Parent $PSScriptRoot
$failed = 0

foreach ($exe in $Blender) {
    if (-not (Test-Path $exe)) {
        Write-Host "SKIP (not installed): $exe"
        continue
    }
    $name = (Get-Item $exe).VersionInfo.ProductVersion
    Write-Host "=== $exe ==="

    & $exe -b $Blend --python-exit-code 1 --python (Join-Path $PSScriptRoot 'test_maintenance_phase1.py')
    if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: maintenance phase 1 on $name"; $failed++ }

    & $exe -b $Blend --python-exit-code 1 --python (Join-Path $root 'scratch\test_milestone3_acceptance.py')
    if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: milestone 3 acceptance on $name"; $failed++ }
}

if ($failed -gt 0) {
    Write-Host "$failed suite(s) failed"
    exit 1
}
Write-Host "All suites passed"
exit 0
