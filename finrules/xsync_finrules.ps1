# ================================
# Nuitka Sync Script for vPyFin314
# ================================
# Mirrors __finofx → __finofx_nuitka
# Preserves directory structure
# Copies new/updated files only
# ================================

$ErrorActionPreference = "Stop"

Write-Host "=== Syncing finrules for Nuitka build ===" -ForegroundColor Cyan

# Root project directory (auto-detect based on script location)
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

$src = Join-Path $root "__finofx"
$dst = Join-Path $root "__finofx_nuitka"

if (!(Test-Path $src)) {
    Write-Host "ERROR: Source directory not found: $src" -ForegroundColor Red
    exit 1
}

if (!(Test-Path $dst)) {
    Write-Host "Creating Nuitka build directory: $dst" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $dst | Out-Null
}

# List of directories to sync
$folders = @(
    "finrules",
    "finrules\rules",
    "finrules\icons",
    "finrules\themes"
)

foreach ($folder in $folders) {

    $srcFolder = Join-Path $src $folder
    $dstFolder = Join-Path $dst $folder

    if (!(Test-Path $srcFolder)) {
        Write-Host "Skipping missing folder: $srcFolder" -ForegroundColor DarkYellow
        continue
    }

    if (!(Test-Path $dstFolder)) {
        Write-Host "Creating folder: $dstFolder" -ForegroundColor Yellow
        New-Item -ItemType Directory -Path $dstFolder | Out-Null
    }

    Write-Host "Syncing: $folder" -ForegroundColor Green

    # Copy updated files only
    robocopy $srcFolder $dstFolder /E /XO /NFL /NDL /NJH /NJS | Out-Null
}

Write-Host "=== Sync Complete ===" -ForegroundColor Cyan
