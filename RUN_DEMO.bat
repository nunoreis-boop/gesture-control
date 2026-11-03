@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto ready
py -3.11 -m venv .venv 2>nul
if not errorlevel 1 goto ready
python -m venv .venv
if errorlevel 1 goto failed
:ready
".venv\Scripts\python.exe" windows_tools.py demo
if errorlevel 1 goto failed
pause
exit /b 0
:failed
echo.
echo Setup failed. Check the messages above. Python 3.11 is required.
pause
exit /b 1
