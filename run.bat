@echo off
echo [🧬 The Breeding Vat] Launching Lab in Docker...

:: 1. Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Docker is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)

:: 2. Run the UI Container
:: We mount the Docker socket so the container can launch sibling containers.
:: We pass the current directory as HOST_PWD so sibling containers mount correctly.
echo Starting the Control Room...
docker run --rm -it ^
    -p 8501:8501 ^
    -v //var/run/docker.sock:/var/run/docker.sock ^
    -v "%cd%:/app" ^
    -e HOST_PWD="%cd%" ^
    --gpus all ^
    vat-ui

pause
