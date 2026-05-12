@echo off
REM Quick setup for The Breeding Vat on Windows

setlocal enabledelayedexpansion

echo.
echo 🧪 The Breeding Vat - Docker Setup
echo ====================================
echo.

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker not found. Please install Docker Desktop.
    pause
    exit /b 1
)

echo ✅ Docker found

REM Check docker-compose
docker compose version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose not found. Please update Docker Desktop.
    pause
    exit /b 1
)

echo ✅ Docker Compose found

REM Build images
echo.
echo 📦 Building Docker images (this may take 5-10 minutes)...
docker compose -f docker/docker-compose.yml build

if errorlevel 1 (
    echo ❌ Build failed
    pause
    exit /b 1
)

echo.
echo ✅ Setup complete!
echo.
echo Next steps:
echo   1. Start UI:  docker compose -f docker/docker-compose.yml up -d breeding-vat-ui
echo   2. Open:      http://localhost:8501
echo   3. Stop:      docker compose -f docker/docker-compose.yml down
echo.
pause
