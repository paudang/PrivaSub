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
**Cause:** Windows lists multiple sound devices, virtual cables, and hardware outputs. The currently selected audio source may be inactive or mismatched with your actual output device.

**Solution:** PrivaSub provides an intuitive **Audio Source** selector directly in the System Tray menu. Follow these rules to select the correct device:

::: tip Selecting the Correct Audio Source
Right-click the PrivaSub icon in your Windows System Tray (taskbar) -> Hover over **Audio Source** and select the device based on your use case:

1. **Capturing System Audio (Zoom, Teams, YouTube, Browser):**
   * Select a device with the `[Loopback]` prefix.
   * **Listening via Laptop/Desktop Speakers:** Choose `[Loopback] Speakers (Realtek(R) Audio)` or your primary monitor output.
   * **Listening via Headset / AirPods / Bluetooth:** Choose `[Loopback] Headset Earphone` or `[Loopback] Headphones`.

2. **Capturing Your Own Voice (Microphone):**
   * Select a device with the `[Mic]` prefix.
   * **Using Built-in Mic:** Choose `[Mic] Microphone Array (Realtek(R) Audio)`.
   * **Using External Mic / Headset Mic:** Choose `[Mic] Headset Microphone` or your dedicated USB microphone.
:::

::: warning Important Notes on Device Switching
* **Switching Output Devices in Meetings:** If you plug in your headset or switch from speakers to Bluetooth headphones mid-meeting, make sure to open the **Audio Source** menu in PrivaSub and select the corresponding `[Loopback]` device.
* **Silero VAD (Voice Activity Detector):** PrivaSub uses an intelligent AI filter to keep CPU usage near 0%. If the audio contains only background music, silence, or non-speech noise, the transcriber intentionally remains idle until distinct speech is detected.
:::

### 2. Subtitles window is off-screen or invisible
**Symptom:** You hear a beep indicating the app started, but you cannot see the subtitle overlay.  
**Solution:** 
Right-click the PrivaSub icon in the System Tray (bottom right of your screen) and click **Settings**. The Settings window is smart and will spawn on your active monitor. In the Settings window, click **Reset Defaults** (if available) or adjust the Opacity slider to ensure it is visible.

### 3. Application says "PrivaSub is already running!"
**Symptom:** You try to open PrivaSub and get this warning.  
**Solution:** PrivaSub enforces a single-instance limit to save system resources. Look for the PrivaSub icon in your System Tray. If the app is stuck, you can force close `python.exe` or `pythonw.exe` from the Windows Task Manager.
