@echo off
setlocal enabledelayedexpansion
set "APP_PORT=8001"
set "FOUND=0"

echo Stopping School Election App...

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%APP_PORT% " ^| findstr LISTENING') do (
    echo Stopping app on port %APP_PORT% PID %%a...
    taskkill /F /PID %%a >nul 2>&1
    set "FOUND=1"
)

taskkill /F /IM school-election-app.exe /T >nul 2>&1
if not errorlevel 1 set "FOUND=1"

if "!FOUND!"=="1" (
    echo Application stopped successfully.
) else (
    echo No running instance found or application already stopped.
)

timeout /t 2 >nul
