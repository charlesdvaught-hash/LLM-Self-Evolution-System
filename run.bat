@echo off
echo [🧬 The Breeding Vat] Launching Lab in Docker...

:: 1. Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Docker is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)

:: 2. Run the UI Container via Manager
:: The manager script handles port collisions and container lifecycle.
python scripts/manager.py run

pause
