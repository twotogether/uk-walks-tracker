@echo off
REM One-click build script for UK Walks Tracker (Windows)
REM This script builds the entire project in one command

setlocal enabledelayedexpansion

cd /d "%~dp0"

echo.
echo ============================================================
echo   UK Walks Tracker - One-Click Build (Windows)
echo ============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python or add it to your PATH
    pause
    exit /b 1
)

REM Run the build script with arguments
if "%1"=="" (
    echo Running standard build...
    echo.
    python scripts\build.py
) else if "%1"=="--clean" (
    echo Running clean build...
    echo.
    python scripts\build.py --clean
) else if "%1"=="--preview" (
    echo Running build with preview...
    echo.
    python scripts\build.py --preview
) else if "%1"=="--help" (
    python scripts\build.py --help
) else (
    echo Unknown option: %1
    echo.
    echo Usage:
    echo   build.bat              - Standard build
    echo   build.bat --clean      - Clean build (removes old artifacts^)
    echo   build.bat --preview    - Build and open in browser
    echo   build.bat --help       - Show help message
    echo.
    pause
    exit /b 1
)

if %errorlevel% neq 0 (
    echo.
    echo Build failed! Check the output above for details.
    pause
    exit /b 1
)

echo.
echo Build completed successfully!
pause
