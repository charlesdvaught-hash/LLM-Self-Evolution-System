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

:: Install base requirements
echo Installing core dependencies...
pip install -r requirements.txt

:: Initialize database
echo Initializing database...
python -c "from breeding_vat.orchestrator.runner import TaskRunner; TaskRunner()"

:: Build UI container (optional, can also run locally)
echo Building UI container...
docker build -t breeding-vat-ui .

echo.
echo [✓] Setup Complete.
echo To start the app, run: streamlit run breeding_vat/ui/app.py
pause
