@echo off
REM Launcher for the Vens Model Configurator GUI
REM Change to the parent of this folder so Python can import the `vens` package
pushd "%~dp0\.."
python -m vens.configurator.gui
popd
pause
