@echo off
echo [🧬 The Breeding Vat] Initializing Lab...

:: 1. Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Docker is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)

:: 2. Run the UI Container via Manager
:: The manager script handles image verification/repair, port collisions, and container lifecycle.
python scripts/manager.py run

if %errorlevel% neq 0 (
    echo.
    echo [!] Lab failed to start.
    pause
)
