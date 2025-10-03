@echo off
:: Get the folder of this batch file (the desktop)
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

:: Optional: add batch folder to PATH for this session
set "PATH=%SCRIPT_DIR%;%PATH%"
:: Run the Python script in the same folder as the batch file
py "%SCRIPT_DIR%\exfiltrate.py" %*
