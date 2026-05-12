#!/usr/bin/env bash
# Windows batch script wrapper for The Breeding Vat
# Run this from PowerShell or CMD: .\docker\dev.bat <command>

@echo off
setlocal enabledelayedexpansion

set COMMAND=%1
if "%COMMAND%"=="" set COMMAND=help

cd /d "%~dp0\.."

if "%COMMAND%"=="up" (
    echo 🚀 Starting The Breeding Vat...
    docker compose --file docker/docker-compose.yml up -d
    echo ✅ Services started.
    echo 📊 Streamlit UI: http://localhost:8501
) else if "%COMMAND%"=="down" (
    echo 🛑 Stopping The Breeding Vat...
    docker compose --file docker/docker-compose.yml down
    echo ✅ Services stopped.
) else if "%COMMAND%"=="logs" (
    echo 📋 Streaming logs...
    docker compose --file docker/docker-compose.yml logs -f
) else if "%COMMAND%"=="build" (
    echo 📦 Building images...
    docker compose --file docker/docker-compose.yml build --no-cache
    echo ✅ Build complete.
) else if "%COMMAND%"=="help" (
    echo Usage: .\docker\dev.bat ^<command^>
    echo.
    echo Commands:
    echo   up        Start services
    echo   down      Stop services
    echo   logs      Stream logs
    echo   build     Rebuild images
    echo   help      Show this help
) else (
    echo docker compose --file docker/docker-compose.yml %*
    docker compose --file docker/docker-compose.yml %*
)
