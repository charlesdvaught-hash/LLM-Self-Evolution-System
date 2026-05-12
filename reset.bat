@echo off
setlocal enabledelayedexpansion

echo.
echo =====================================================================
echo [🧬] BREEDING VAT - FULL SYSTEM RESET & RESTART
echo =====================================================================
echo.

echo [1/5] Stopping Docker containers...
for /f "tokens=*" %%A in ('docker ps -a --filter "ancestor=breeding-vat-ui:latest" --format "{{.ID}}" 2^>nul') do (
    docker stop %%A 2>nul
    docker rm %%A 2>nul
    echo [✓] Container removed
)

echo.
echo [2/5] Clearing Python bytecode cache...
setlocal enabledelayedexpansion
for /d /r "breeding_vat" %%D in (__pycache__) do (
    if exist "%%D" (
        rmdir /s /q "%%D" 2>nul
        echo [✓] Removed %%D
    )
)

echo.
echo [3/5] Clearing .pyc and .pyo files...
for /r "breeding_vat" %%F in (*.pyc *.pyo) do (
    if exist "%%F" (
        del "%%F" 2>nul
    )
)

echo.
echo [4/5] Clearing Streamlit cache...
if exist "%APPDATA%\.streamlit" (
    rmdir /s /q "%APPDATA%\.streamlit" 2>nul
    echo [✓] Cleared %APPDATA%\.streamlit
)

echo.
echo [5/5] Verifying system state...
docker images --filter "reference=breeding-vat-ui:*" --format "{{.Repository}} - {{.Size}}" 2>nul
if errorlevel 1 (
    echo [!] Docker images not found - may need rebuild
) else (
    echo [✓] Docker images present
)

echo.
echo =====================================================================
echo [✓] System reset complete!
echo =====================================================================
echo.
echo Next step: run.bat
echo.
