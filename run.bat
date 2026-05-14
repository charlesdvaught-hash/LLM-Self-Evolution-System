@echo off
setlocal enabledelayedexpansion

title The Breeding Vat - Control Room

echo.
echo  ^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=
echo    The Breeding Vat [LLM Evolution Lab]
echo  ^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=
echo.

REM Check if Docker is running
echo [*] Checking Docker daemon...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Docker is not running.
    echo     Please start Docker Desktop and try again.
    echo.
    pause
    exit /b 1
)
echo [OK] Docker is running.
echo.

REM Launch Control Room
echo [*] Starting Control Room...
echo     (Reuses container if running)
echo.
python scripts/manager.py run

if %errorlevel% neq 0 (
    echo.
    echo [!] Lab failed to start.
    echo     Run: setup.bat
    echo     to build all images and download models.
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] Control Room stopped.
pause
