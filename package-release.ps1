# Build the portable exe (settings, static, templates, and signed license are bundled inside).
param(
    [Parameter(Mandatory = $true)][string]$SchoolName,
    [Parameter(Mandatory = $true)][int]$ValidDays,
    [Parameter(Mandatory = $true)][string]$LicenseeId,
    [string]$DeveloperName = "EmpowerID",
    [string]$DeveloperContact = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if ($ValidDays -le 0) {
    throw "ValidDays must be greater than 0."
}

$pythonExe = "$root\venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    throw "Python not found at $pythonExe. Create venv first."
}

Write-Host "Generating signed school license..."
$licenseArgs = @(
    "$root\tools\generate_license.py",
    "--school-name", $SchoolName,
    "--valid-days", $ValidDays,
    "--licensee-id", $LicenseeId,
    "--developer-name", $DeveloperName,
    "--key-path", "$root\tools\.license-signing-key",
    "--out", "$root\build\license_embed.py"
)
if ($DeveloperContact) {
    $licenseArgs += @("--developer-contact", $DeveloperContact)
}
& $pythonExe @licenseArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (-not (Test-Path "$root\settings\config.json")) {
    throw "settings/config.json not found. Create it before building the exe."
}

Write-Host "Building executable (edit settings/config.json and settings/candidates.json before this)..."
& $pythonExe -m PyInstaller --noconfirm school-election-app.spec
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$release = Join-Path $root "release"
if (Test-Path $release) { Remove-Item $release -Recurse -Force }
New-Item -ItemType Directory -Path $release | Out-Null
Copy-Item "$root\dist\school-election-app.exe" $release

Write-Host ""
Write-Host "Release folder ready:"
Write-Host "  $release\school-election-app.exe"
Write-Host ""
Write-Host "Copy the exe to each client laptop. No static or settings folders needed."
Write-Host "votes.xlsx is created beside the exe on first vote."
Write-Host ""
Write-Host "Optional: put config.json or settings/config.json beside the exe to change school name, node_role, sync_secret, admin password, or candidates on that machine."
Write-Host "License embedded for school: $SchoolName (valid $ValidDays days from first launch per laptop)."
