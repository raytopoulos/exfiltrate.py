@echo off
curl -o python-installer.exe https://www.python.org/ftp/python/3.13.7/python-3.13.7-amd64.exe
python-installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0

py -m pip install pywinauto

set "CURRENT_DIR=%~dp0"
if "%CURRENT_DIR:~-1%"=="\" set "CURRENT_DIR=%CURRENT_DIR:~0,-1%"

:: Read USER PATH from registry
set "USER_PATH="
for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul ^| findstr "Path"') do (
    set "USER_PATH=%%B"
)

:: Check if CURRENT_DIR is already in USER_PATH
echo %USER_PATH% | find /I "%CURRENT_DIR%" >nul
if %ERRORLEVEL%==0 (
    echo Folder is already in the user PATH.
    pause
    goto :EOF
)

:: Append current folder to USER_PATH
if defined USER_PATH (
    set "NEW_PATH=%USER_PATH%;%CURRENT_DIR%"
) else (
    set "NEW_PATH=%CURRENT_DIR%"
)

:: Write new PATH to registry
reg add "HKCU\Environment" /v Path /t REG_EXPAND_SZ /d "%NEW_PATH%" /f

:: Update current CMD session PATH
set "PATH=%NEW_PATH%"

:: Notify system to propagate PATH change
powershell -Command "[Environment]::SetEnvironmentVariable('Path', '%NEW_PATH%', 'User'); $signature = '[DllImport(\"user32.dll\")]public static extern int SendMessageTimeout(int hWnd, int Msg, int wParam, int lParam, int fuFlags, int uTimeout, out int lpdwResult);'; $type = Add-Type -MemberDefinition $signature -Name 'Win32SendMessageTimeout' -Namespace Win32Functions -PassThru; $result = 0; $type::SendMessageTimeout(-1,0x1A,0,0,0,1000,[ref]$result)"

echo Successfully added "%CURRENT_DIR%" to user PATH.
pause
