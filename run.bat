@echo off
echo Stopping any existing background instances of PrivaSub...
taskkill /f /im pythonw.exe >nul 2>&1

echo Starting PrivaSub in background...
:: Check if .venv is present and able to load DLLs (bypasses AppLocker block)
if not exist ".venv\Scripts\python.exe" goto :fallback

".venv\Scripts\python.exe" -c "import av" >nul 2>&1
if errorlevel 1 goto :fallback

start "" ".venv\Scripts\pythonw.exe" "src/main.py"
exit

:fallback
:: Fallback to running with global pythonw if .venv is blocked or missing
start "" "pythonw.exe" "src/main.py"
exit
