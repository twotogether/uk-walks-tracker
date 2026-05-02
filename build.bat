@echo off
REM One-click build script for UK Walks Tracker (Windows)

cd /d "%~dp0"

echo.
echo ============================================================
echo   UK Walks Tracker - One-Click Build (Windows)
echo ============================================================
echo.

REM Try to find Python executable
set PYTHON=python
if exist ".venv\Scripts\python.exe" (
    set PYTHON=.venv\Scripts\python.exe
)

REM Verify Python is available
%PYTHON% --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org
    echo or create a virtual environment with: python -m venv .venv
    pause
    exit /b 1
)

REM Run the build script with arguments
if "%1"=="" (
    echo Running standard build...
    echo.
    %PYTHON% scripts\build.py
    goto end
)

if "%1"=="--clean" (
    echo Running clean build...
    echo.
    %PYTHON% scripts\build.py --clean
    goto end
)

if "%1"=="--preview" (
    echo Running build with preview...
    echo.
    %PYTHON% scripts\build.py --preview
    goto end
)

if "%1"=="--update-only" (
    echo Running update only (skipping Sphinx)...
    echo.
    %PYTHON% scripts\build.py --update-only
    goto end
)

if "%1"=="--help" (
    %PYTHON% scripts\build.py --help
    goto end
)

echo Unknown option: %1
echo.
echo Usage:
echo   build.bat                - Standard build
echo   build.bat --clean        - Clean build
echo   build.bat --preview      - Build and open in browser
echo   build.bat --update-only  - Update walks.yaml and map only
echo   build.bat --help         - Show help message
echo.
pause
exit /b 1

:end
if errorlevel 1 (
    echo.
    echo Build failed! Check the output above for details.
    pause
    exit /b 1
)

echo.
echo Build completed successfully!
pause
