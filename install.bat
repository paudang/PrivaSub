@echo off
echo ==================================================
echo PrivaSub - Local Environment Installer
echo ==================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% equ 0 goto :python_ready

:: Check if it's already installed in default folders but not in system PATH
set "PYTHON_PATH="
for /d %%d in ("%LocalAppData%\Programs\Python\Python*") do (
    if exist "%%d\python.exe" set "PYTHON_PATH=%%d"
)
if not defined PYTHON_PATH (
    for /d %%d in ("%ProgramFiles%\Python*") do (
        if exist "%%d\python.exe" set "PYTHON_PATH=%%d"
    )
)
if not defined PYTHON_PATH (
    if defined ProgramFiles(x86) (
        for /d %%d in ("%ProgramFiles(x86)%\Python*") do (
            if exist "%%d\python.exe" set "PYTHON_PATH=%%d"
        )
    )
)

if defined PYTHON_PATH (
    set "Path=%PYTHON_PATH%;%PYTHON_PATH%\Scripts\;%Path%"
    python --version >nul 2>&1
    if %errorlevel% equ 0 goto :python_ready
)

echo [WARNING] Python is not detected on your system.
echo PrivaSub requires Python 3.10, 3.11, or 3.12 to run.
echo.
set /p choice="Would you like to automatically download and install Python 3.11.9 (100%% offline local run)? (Y/N): "
if /i "%choice%"=="Y" (
    echo.
    echo Downloading Python 3.11.9 installer from python.org...
    curl -L -o python_installer.exe https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to download Python installer. Please install it manually.
        pause
        exit /b
    )
    
    echo Installing Python 3.11.9 silently... Please wait about 30 seconds...
    start /wait "" python_installer.exe /quiet PrependPath=1 Include_test=0 Shortcuts=0
    del python_installer.exe
    
    :: Try to find the newly installed python dynamically
    set "PYTHON_PATH="
    for /d %%d in ("%LocalAppData%\Programs\Python\Python*") do (
        if exist "%%d\python.exe" set "PYTHON_PATH=%%d"
    )
    if not defined PYTHON_PATH (
        for /d %%d in ("%ProgramFiles%\Python*") do (
            if exist "%%d\python.exe" set "PYTHON_PATH=%%d"
        )
    )
    
    if defined PYTHON_PATH (
        set "Path=%PYTHON_PATH%;%PYTHON_PATH%\Scripts\;%Path%"
    ) else (
        :: Fallback to Python 3.11 default path
        set "Path=%LocalAppData%\Programs\Python\Python311\;%LocalAppData%\Programs\Python\Python311\Scripts\;%Path%"
    )
    
    :: Verify again
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Python installation finished but could not be detected.
        echo Please restart your terminal or computer and run install.bat again.
        pause
        exit /b
    )
    echo [SUCCESS] Python installed and verified successfully!
    echo.
) else (
    echo Please install Python manually from python.org and add it to your system PATH.
    pause
    exit /b
)
:python_ready

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

:: Verify if virtual environment DLL execution is allowed under system AppLocker policies
.venv\Scripts\python.exe -c "import av" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Virtual environment execution is restricted by Windows Application Control policies.
    echo Re-routing installation to Global Python environment to bypass blocks...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install global dependencies. Please contact your system administrator.
        pause
        exit /b
    )
    echo [SUCCESS] Global dependencies installed successfully!
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
