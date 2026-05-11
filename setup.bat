@echo off
echo [🧬 The Breeding Vat] Initializing Setup...

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Please install Python 3.10+.
    exit /b 1
)

:: Check for Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker not found. Docker is required for isolation.
    exit /b 1
)

:: Install base requirements for the Host (UI and Orchestrator)
echo Installing core dependencies...
pip install streamlit transformers torch accelerate pyyaml pandas

:: Initialize database
echo Initializing database...
python -c "from breeding_vat.orchestrator.runner import TaskRunner; TaskRunner()"

:: Build specialized containers
echo Building module containers...
docker build -t vat-merge -f docker/Dockerfile.merge .
docker build -t vat-eval -f docker/Dockerfile.eval .
docker build -t vat-sae -f docker/Dockerfile.sae .

echo.
echo [✓] Setup Complete.
echo To start the app, run: run.bat
pause
