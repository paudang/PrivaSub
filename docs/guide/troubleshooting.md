# Troubleshooting

If you encounter issues while installing or running PrivaSub, check the common solutions below.

## Installation Issues

### 1. "DLL load failed" when installing dependencies (PyAV or CTranslate2)
**Symptom:** During installation or when running the app, Python crashes with an error saying a required DLL could not be found or loaded.  
**Cause:** Some enterprise environments, Windows Defender Application Control (WDAC), or AppLocker policies prevent DLL files from being executed from user workspace directories (like `.venv`).  
**Solution:** 
The provided `install.bat` automatically detects this and falls back to installing dependencies into the **Global Python Environment**. If you are installing manually, do not use a virtual environment. Instead, install the dependencies directly:
```bash
python -m pip install -r requirements.txt
```

### 2. Missing Python in System PATH
**Symptom:** Running `python --version` returns an error.  
**Solution:** Reinstall Python and ensure you check the box **"Add Python to PATH"** at the bottom of the installer window.

## Runtime Issues

### 1. App does not capture system audio
**Symptom:** The app starts, but no subtitles appear even when audio is playing.  
**Cause:** The default audio device on Windows might not support WASAPI Loopback, or the app doesn't have permission to record audio.  
**Solution:** Ensure your primary Speakers/Headphones are set as the default output device in Windows Sound Settings.

### 2. Subtitles window is off-screen or invisible
**Symptom:** You hear a beep indicating the app started, but you cannot see the subtitle overlay.  
**Solution:** 
Right-click the PrivaSub icon in the System Tray (bottom right of your screen) and click **Settings**. The Settings window is smart and will spawn on your active monitor. In the Settings window, click **Reset Defaults** (if available) or adjust the Opacity slider to ensure it is visible.

### 3. Application says "PrivaSub is already running!"
**Symptom:** You try to open PrivaSub and get this warning.  
**Solution:** PrivaSub enforces a single-instance limit to save system resources. Look for the PrivaSub icon in your System Tray. If the app is stuck, you can force close `python.exe` or `pythonw.exe` from the Windows Task Manager.
