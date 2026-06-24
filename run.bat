@echo off
echo Starting PrivaSub in background...
:: Check if .venv is present and able to load DLLs (bypasses AppLocker block)
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import av" >nul 2>&1
    if %errorlevel% equ 0 (
        start "" ".venv\Scripts\pythonw.exe" "src/main.py"
        exit
    )
)

:: Fallback to running with global pythonw if .venv is blocked or missing
start "" "pythonw.exe" "src/main.py"
exit
