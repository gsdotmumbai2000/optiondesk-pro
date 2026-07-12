#Requires -Version 5.1
<#
.SYNOPSIS
    Build OptionDesk Pro Windows executable with PyInstaller.

.DESCRIPTION
    Produces dist/OptionDeskPro.exe (single-file GUI binary).
    User data is stored under %LOCALAPPDATA%\OptionDeskPro.

.EXAMPLE
    .\scripts\build_windows.ps1
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "==> OptionDesk Pro Windows build" -ForegroundColor Cyan

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Pip = Join-Path $Root ".venv\Scripts\pip.exe"

Write-Host "==> Installing package and build tools" -ForegroundColor Cyan
& $Pip install --upgrade pip setuptools wheel | Out-Null
& $Pip install -e ".[build]" | Out-Null

Write-Host "==> Running PyInstaller" -ForegroundColor Cyan
& $Python -m PyInstaller --noconfirm --clean (Join-Path $Root "build\windows\optiondesk.spec")

$Exe = Join-Path $Root "dist\OptionDeskPro.exe"
if (-not (Test-Path $Exe)) {
    throw "Build failed: $Exe was not created"
}

$SizeMb = [math]::Round((Get-Item $Exe).Length / 1MB, 1)
Write-Host ""
Write-Host "Build complete:" -ForegroundColor Green
Write-Host "  $Exe"
Write-Host "  Size: ${SizeMb} MB"
Write-Host ""
Write-Host "Run: .\dist\OptionDeskPro.exe"
