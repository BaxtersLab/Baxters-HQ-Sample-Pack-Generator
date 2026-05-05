@echo off
setlocal

cd /d "%~dp0"

:: ── Try project venv first ────────────────────────────────────────────────
if exist ".venv\Scripts\python.exe" (
    set PYTHON=".venv\Scripts\python.exe"
    goto :launch
)

:: ── Fall back to system Python ────────────────────────────────────────────
if exist "C:\Python314\python.exe" (
    set PYTHON="C:\Python314\python.exe"
    goto :launch
)

:: ── python.exe on PATH ────────────────────────────────────────────────────
where python >nul 2>&1
if %errorlevel%==0 (
    set PYTHON=python
    goto :launch
)

echo ERROR: No Python interpreter found.
echo Install Python or create a .venv in this folder.
pause
exit /b 1

:launch
echo Starting Baxters HQ Sample Pack Generator...
%PYTHON% run_gui.py
if %errorlevel% neq 0 (
    echo.
    echo App exited with error code %errorlevel%.
    pause
)
endlocal
