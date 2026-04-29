@echo off
title VENS STARTUP PROTOCOL v1.0
color 0B

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║          VENS STARTUP PROTOCOL v1.0                 ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

:: ──────────────────────────────────────────────────────────
:: STEP 1: Open VS Code into the Vens workspace
:: ──────────────────────────────────────────────────────────
echo  [1/4] Opening VS Code workspace...
code "%~dp0.." 2>nul
if errorlevel 1 (
    echo  ⚠  VS Code not found in PATH. Please open the workspace manually.
) else (
    echo        ✅ VS Code launched
)
echo.

:: ──────────────────────────────────────────────────────────
:: STEP 2: Open the Setup Wizard for the user to fill in
:: ──────────────────────────────────────────────────────────
echo  [2/4] Opening Setup Wizard...
if exist "%~dp0SETUP_WIZARD.txt" (
    code "%~dp0SETUP_WIZARD.txt" 2>nul
    if errorlevel 1 (
        notepad "%~dp0SETUP_WIZARD.txt"
    )
    echo        ✅ SETUP_WIZARD.txt opened
) else (
    echo  ⚠  SETUP_WIZARD.txt not found!
    pause
    exit /b 1
)
echo.

:: ──────────────────────────────────────────────────────────
:: STEP 3: Wait for user to fill in the wizard
:: ──────────────────────────────────────────────────────────
echo  ══════════════════════════════════════════════════════
echo.
echo   📝 Fill in SETUP_WIZARD.txt with your project details.
echo      Save the file when you're done (Ctrl+S).
echo.
echo   When you have saved the file, press any key to continue...
echo.
echo  ══════════════════════════════════════════════════════
pause >nul

:: ──────────────────────────────────────────────────────────
:: STEP 4: Apply the setup and start the orchestrator
:: ──────────────────────────────────────────────────────────
echo.
echo  [3/4] Applying your setup to the Vens system...
echo.
node "%~dp0apply_setup.js"
if errorlevel 1 (
    echo.
    echo  ❌ Setup failed. Please check SETUP_WIZARD.txt and try again.
    pause
    exit /b 1
)

echo.
echo  [4/4] Starting the Vens Orchestrator...
echo.
node "%~dp0orchestrator.js"
