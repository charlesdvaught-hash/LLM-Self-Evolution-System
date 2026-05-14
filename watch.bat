@echo off
setlocal enabledelayedexpansion

title The Breeding Vat - Live Watch

echo.
echo  ^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=
echo    Live Watch - Auto-sync changes as you code
echo  ^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Docker is not running.
    echo     Please start Docker Desktop and try again.
    echo.
    pause
    exit /b 1
)

echo [*] Watching for changes... (syncing every 2 seconds)
echo [*] Leave this window open while you code.
echo [*] Press Ctrl+C to stop watching.
echo.
python scripts/manager.py watch

if %errorlevel% neq 0 (
    echo.
    echo [!] Watch failed.
    echo     Make sure the container is running: run.bat
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] Watch stopped.
pause
