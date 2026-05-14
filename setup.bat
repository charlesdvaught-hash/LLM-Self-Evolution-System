@echo off
setlocal enabledelayedexpansion

title The Breeding Vat - Setup & Initialize

echo.
echo  ^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=
echo    The Breeding Vat [Initial Setup]
echo  ^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=
echo.
echo This initializes the environment from scratch.
echo - Builds Docker images (~10-15 min)
echo - Downloads model specimens from HuggingFace (~15-30 min)
echo.

REM Check for Docker
echo [*] Checking for Docker Desktop...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Docker Desktop not found.
    echo     Install from: https://www.docker.com/products/docker-desktop/
    echo.
    pause
    exit /b 1
)
echo [OK] Docker is installed.
echo.

REM Run setup
echo [*] Starting setup...
echo.
python scripts/manager.py setup

if %errorlevel% neq 0 (
    echo.
    echo [X] Setup failed.
    echo     Possible causes:
    echo       - Docker daemon not running
    echo       - Insufficient disk space (need ~25GB total)
    echo       - Network issues (model downloads)
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] Setup complete!
echo.
echo Next: Run run.bat to start the Control Room
echo.
pause
