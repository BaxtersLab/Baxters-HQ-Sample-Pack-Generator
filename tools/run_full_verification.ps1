<#
Run Full Runtime Verification for HQSPG (PowerShell)

Usage: run from repository root in PowerShell (preferably elevated ExecutionPolicy for the session):
  .\tools\run_full_verification.ps1

This script will:
  - create a fresh venv at `.venv` (if missing)
  - install `requirements.txt`
  - run `pytest -q`
  - launch the GUI (waits for user to close it)
  - optionally build the EXE with PyInstaller

Notes:
  - Run this interactively; the script pauses for confirmation before launching GUI and before building the EXE.
  - If you want to test resume semantics, kill the GUI process mid-run with Task Manager or Ctrl+C in the console if running in-window.
#>
param()

function Confirm-Or-Exit($msg){
    Write-Host "`n$msg [Y/n]" -ForegroundColor Cyan -NoNewline
    $ans = Read-Host
    if($ans -ne '' -and $ans.ToLower().StartsWith('n')){
        Write-Host "Aborting per user request." -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "HQSPG Full Runtime Verification Script" -ForegroundColor Green

# 1) Create venv
if(-Not (Test-Path -Path ".venv")){
    Write-Host "Creating virtual environment .venv..." -ForegroundColor Green
    python -m venv .venv
} else {
    Write-Host ".venv already exists — skipping creation." -ForegroundColor Yellow
}

# Activate the venv for the remainder of the script
Write-Host "Activating .venv..." -ForegroundColor Green
. .\.venv\Scripts\Activate.ps1

# 2) Install requirements
Write-Host "Installing requirements from requirements.txt..." -ForegroundColor Green
pip install -r requirements.txt

# 3) Run tests
Write-Host "Running test suite (pytest -q)..." -ForegroundColor Green
try{
    pytest -q
} catch {
    Write-Host "pytest exited with a non-zero status. Inspect failures, fix, then re-run." -ForegroundColor Red
    Confirm-Or-Exit "Continue to GUI launch despite test failures?"
}

# 4) Launch GUI
Confirm-Or-Exit "Ready to launch the GUI. Ensure you have audio test files available. Launch now?"

Write-Host "Launching GUI: python -m gui.main" -ForegroundColor Green
try{
    # Run in the same console so logs are visible. If you prefer a new window, replace with Start-Process
    python -m gui.main
} catch {
    Write-Host "GUI exited with error: $_" -ForegroundColor Red
}

Write-Host "GUI closed or exited." -ForegroundColor Green

# 5) Optionally build EXE
Confirm-Or-Exit "Build Windows EXE with PyInstaller now? (requires pyinstaller installed in this venv)"

if(-Not (Get-Command pyinstaller -ErrorAction SilentlyContinue)){
    Write-Host "PyInstaller not found; installing..." -ForegroundColor Green
    pip install pyinstaller
}

Write-Host "Running: pyinstaller hqspg_gui.spec" -ForegroundColor Green
pyinstaller hqspg_gui.spec

Write-Host "Build finished. Run the EXE from 'dist\hqspg_gui\hqspg_gui.exe' and verify runtime behavior." -ForegroundColor Green

Write-Host "Full runtime verification script completed." -ForegroundColor Cyan
