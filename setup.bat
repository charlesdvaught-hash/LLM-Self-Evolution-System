@echo off
setlocal enabledelayedexpansion
echo [🧬 The Breeding Vat] Windows 11 One-Click Setup...

:: 1. Check for Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Docker Desktop not found.
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

:: 2. Build/Verify All Containers via Manager
python scripts/manager.py verify

echo.
echo [✓] Setup Process Complete!
pause
