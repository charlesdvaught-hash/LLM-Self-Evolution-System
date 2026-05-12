@echo off
setlocal enabledelayedexpansion

title The Breeding Vat - Setup & Repair

echo.
echo  =====================================================================
echo    The Breeding Vat [Setup / Repair Utility]
echo  =====================================================================
echo.

:: 1. Check for Docker
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

:: 2. Environment repair/setup
echo [*] Repairing/verifying Docker images...
echo     (Rebuilds missing images, cleans old containers)
echo.
python scripts/manager.py repair

if %errorlevel% neq 0 (
    echo.
    echo [X] Repair failed. Check Docker daemon and disk space.
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] All images verified/rebuilt successfully!
echo.
echo Next: Run run.bat to start the Control Room
echo.
pause
