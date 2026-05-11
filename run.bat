@echo off
echo [🧬 The Breeding Vat] Launching Lab...

:: 1. Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Docker is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)

:: 2. Activate Venv and Run
if exist "venv\Scripts\activate" (
    call venv\Scripts\activate
    streamlit run breeding_vat/ui/app.py
) else (
    echo [!] Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)
