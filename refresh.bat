@echo off
echo Stopping School Election App...
taskkill /F /IM school-election-app.exe /T
if %ERRORLEVEL% EQU 0 (
    echo Application stopped successfully.
) else (
    echo No running instance found or application already stopped.
)
timeout /t 2 >nul

echo Starting School Election App...
start "" "school-election-app.exe"
echo Application started successfully.
