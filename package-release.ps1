# Build the portable exe (settings, static, templates are bundled inside).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host "Building executable (edit settings/config.example.json and settings/candidates.json before this)..."
& "$root\venv\Scripts\python.exe" -m PyInstaller --noconfirm school-election-app.spec
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
Write-Host "Optional: put config.json beside the exe to override node_role / sync_secret / admin password on that machine."
