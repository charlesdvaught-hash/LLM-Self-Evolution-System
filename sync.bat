@echo off
setlocal enabledelayedexpansion

title The Breeding Vat - Quick Sync

echo.
echo  ^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=
echo    Quick Sync - Push changes to running container
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

echo [*] Syncing changed files to running container...
echo     (No rebuild - changes copied directly)
echo.
python scripts/manager.py sync

if %errorlevel% neq 0 (
    echo.
    echo [!] Sync failed.
    echo     Make sure the container is running: run.bat
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] Sync complete. Refresh your browser.
pause
