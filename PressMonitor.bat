@echo off
:: BatchGotAdmin (Run as Admin code starts)
net session >nul 2>&1
if %errorLevel% == 0 (
    goto gotAdmin
) else (
    goto UACPrompt
)

:UACPrompt
echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
"%temp%\getadmin.vbs"
exit /B

:gotAdmin
if exist "%temp%\getadmin.vbs" (del "%temp%\getadmin.vbs")
:: Run your command that requires admin rights here
echo Running main.exe as Administrator...
cd /d "%~dp0"
"%~dp0main.exe"
pause
