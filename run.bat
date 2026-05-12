@echo off
setlocal enabledelayedexpansion

title The Breeding Vat - Control Room

echo.
echo  ^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=
echo    The Breeding Vat [LLM Evolution Lab]
echo  ^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=
echo.

:: 1. Check if Docker is running
echo [*] Checking Docker daemon...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Docker is not running.
    echo     Please start Docker Desktop and try again.
    echo.
    pause
    exit /b 1
)
echo [OK] Docker is running.
echo.

:: 2. Ask which UI to use
echo [*] Choose UI version:
echo.
echo    1. STABLE: Original (current default)
echo       - Fully tested and working
echo       - All features operational
echo.
echo    2. SLEEK: Dark Theme (experimental)
echo       - Broad-stroke calibration
echo       - Clean 5-tab layout
echo       (Still being tested)
echo.
echo    3. DUAL-MODE: Granular + Exploratory (in development)
echo       - Granular control OR AI orchestration
echo       - Resource transparency
echo       - Not yet stable
echo.
set /p UI_CHOICE="Select (1-3, default=1): "
if "%UI_CHOICE%"=="" set UI_CHOICE=1

if "%UI_CHOICE%"=="1" (
    set UI_SOURCE=breeding_vat/ui/app_original_backup.py
    echo [OK] Using STABLE original version
) else if "%UI_CHOICE%"=="2" (
    set UI_SOURCE=breeding_vat/ui/app_v2_revamped.py
    echo [OK] Using experimental sleek version
) else if "%UI_CHOICE%"=="3" (
    set UI_SOURCE=breeding_vat/ui/app_v3_dual_mode.py
    echo [OK] Using in-development dual-mode version
) else (
    echo [!] Invalid choice. Using default (STABLE original).
    set UI_SOURCE=breeding_vat/ui/app_original_backup.py
)

echo.

:: 3. Copy selected UI to app.py
echo [*] Preparing UI...
copy /Y "%UI_SOURCE%" "breeding_vat/ui/app.py" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Failed to prepare UI
    pause
    exit /b 1
)
echo [OK] UI ready.
echo.

:: 4. Launch via Manager (smart reuse, builds if needed)
echo [*] Starting Control Room...
echo     (This reuses existing container if healthy, or builds if needed)
echo.
python scripts/manager.py run

if %errorlevel% neq 0 (
    echo.
    echo [!] Lab failed to start.
    echo     Run: setup.bat
    echo     to rebuild all images and fix errors.
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] Control Room stopped.
pause
