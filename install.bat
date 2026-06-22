@echo off
echo ==================================================
echo PrivaSub - Local Environment Installer
echo ==================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to your system PATH.
    echo Please install Python recommended 3.10, 3.11, or 3.12 from python.org first.
    echo Make sure to check the box "Add Python to PATH" during installation.
    echo.
    pause
    exit /b
)

echo [1/3] Creating Python Virtual Environment (.venv)...
python -m venv .venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b
)

echo [2/3] Upgrading pip...
.venv\Scripts\python.exe -m pip install --upgrade pip

echo [3/3] Installing dependencies from requirements.txt...
.venv\Scripts\pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b
)

echo.
echo ==================================================
echo Installation completed successfully!
echo.
echo You can now start PrivaSub by double-clicking:
echo   run.bat
echo ==================================================
echo.
pause
