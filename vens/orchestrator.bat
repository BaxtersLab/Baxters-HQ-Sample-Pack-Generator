@echo off
REM Workspace orchestrator: runs the Vens configurator GUI or performs maintenance
python "%~dp0\orchestrator.py" %*
pause
