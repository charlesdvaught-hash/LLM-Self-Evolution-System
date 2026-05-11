@echo off
setlocal enabledelayedexpansion
echo [🧬 The Breeding Vat] Windows 11 One-Click Setup...

:: 1. Check for Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Docker Desktop not found.
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop/
    echo Ensure "Expose daemon on tcp://localhost:2375 without TLS" is NOT needed,
    echo but Docker must be running.
    pause
    exit /b 1
)

:: 2. Build All Containers
echo [i] Building all containers (This will take a while, but keeps your host clean)...
docker build -t vat-ui -f docker/Dockerfile.ui .
docker build -t vat-merge -f docker/Dockerfile.merge .
docker build -t vat-eval -f docker/Dockerfile.eval .
docker build -t vat-sae -f docker/Dockerfile.sae .

echo.
echo [✓] Setup Complete!
echo All dependencies are containerized. Use run.bat to start.
pause
