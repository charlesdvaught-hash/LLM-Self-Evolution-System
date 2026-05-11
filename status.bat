@echo off
setlocal enabledelayedexpansion

title The Breeding Vat - Status Check

echo.
echo  ^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=
echo    The Breeding Vat [System Status]
echo  ^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=^=
echo.

echo [*] Checking Docker...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Docker is not running. Start Docker Desktop.
    goto :end
)
echo [OK] Docker is running.

echo.
echo [*] Checking Breeding Vat images...
docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}" | findstr "breeding-vat"
if %errorlevel% neq 0 (
    echo [!] No Breeding Vat images found. Run setup.bat
    goto :end
)

echo.
echo [*] Checking containers...
docker ps -a --filter "label=breeding_vat=true" --format "table {{.ID}}\t{{.Status}}\t{{.Ports}}"
if %errorlevel% neq 0 (
    echo [!] No containers found.
) else (
    echo [OK] Containers listed above.
)

echo.
echo [*] Running containers...
docker ps --format "table {{.Names}}\t{{.Status}}" | findstr "breeding-vat"
if %errorlevel% neq 0 (
    echo [!] No running Breeding Vat containers.
    echo     Run: run.bat
    echo     to start one.
) else (
    echo [OK] Breeding Vat is running.
)

:end
echo.
pause
