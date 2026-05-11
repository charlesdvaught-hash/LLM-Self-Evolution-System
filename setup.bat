@echo off
setlocal enabledelayedexpansion
echo [🧬 The Breeding Vat] Windows 11 One-Click Setup...

:: 1. Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python 3.10+ not found.
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 2. Check for Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Docker Desktop not found.
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

:: 3. Create Virtual Environment
if not exist "venv" (
    echo [i] Creating virtual environment...
    python -m venv venv
)

:: 4. Install Dependencies
echo [i] Installing host dependencies...
call venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

:: 5. Initialize Database
echo [i] Initializing Lineage Database...
python -c "from breeding_vat.orchestrator.runner import TaskRunner; TaskRunner()"

:: 6. Build Docker Containers
echo [i] Building specialized module containers (This may take a few minutes)...
docker build -t vat-merge -f docker/Dockerfile.merge .
docker build -t vat-eval -f docker/Dockerfile.eval .
docker build -t vat-sae -f docker/Dockerfile.sae .

echo.
echo [✓] Setup Complete!
echo You can now use run.bat to start The Breeding Vat.
pause
