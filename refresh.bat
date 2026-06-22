@echo off
setlocal
set "APP_URL=http://localhost:8001"
set "APP_PORT=8001"

echo Stopping School Election App...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%APP_PORT% " ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)
taskkill /F /IM school-election-app.exe /T >nul 2>&1
timeout /t 2 >nul

echo Starting School Election App...
start "" "%~dp0school-election-app.exe"
echo Waiting for server...
timeout /t 5 >nul

echo Opening browser with cache-busted URL...
start "" "%APP_URL%/?refresh=%RANDOM%"
echo.
echo Tip: If the background still looks old, press Ctrl+Shift+R in the browser.
echo Application restarted successfully.
