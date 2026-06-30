# PrivaSub
> **Offline, Privacy-First Desktop Captions Overlay**

**PrivaSub** is a lightweight, local, and free desktop utility designed to capture system audio (like Zoom meetings, YouTube videos, Teams calls, or VLC players) and transcribe it in real-time onto a premium, transparent overlay. 

Built with privacy at its core, it runs **100% locally on your computer**—requiring zero cloud connections, zero API keys, and absolutely no internet connection after the initial setup.

> [!IMPORTANT]
> **Language Support:** 
> PrivaSub supports live English audio transcription and translation to **10 major world languages** (Vietnamese, Japanese, Chinese Simplified, Chinese Traditional, Korean, Spanish, French, German, Russian, and Thai). You can freely choose between Single Subtitle mode (English Only) or Dual Subtitle mode (original text on top, translation on the bottom). Both speech recognition and translation run 100% offline.

---

## Key Features

*   **Real-Time Multilingual Offline Translation:** Translates English audio on-the-fly into 10 target languages using an optimized offline Meta NLLB-200 model.
*   **Dual Subtitle Layout:** Displays both the original English speech and the translated target text simultaneously.
*   **Anonymous Sub (Screen-Share Stealth Mode):** Advanced Win32 display affinity integration makes the subtitle overlay completely invisible to screen-sharing software (Zoom, Google Meet, Teams, OBS). You can see the subtitles, but your meeting participants will see absolutely nothing!
*   **Zoom-like Text Selection & Omni-Drag Handles:** Easily drag the window using dedicated side grab handles, or freely click inside the box to highlight and copy (`Ctrl + C`) live subtitle text on the fly.
*   **System Tray Integration:** Runs silently in your taskbar (System Tray), keeping your workspace clutter-free.
*   **VAD-Powered Low CPU Usage:** Utilizes *Silero Voice Activity Detection (VAD)*. The transcription engine remains idle (consuming ~0% CPU) during silence or music, triggering only when speech is detected.
*   **Transparent Overlay:** A sleek, borderless, semi-transparent dark subtitle bar that floats on top of all windows.
*   **Click-Through (Lock Mode):** Click right through the subtitles to interact with YouTube buttons or Zoom features underneath.
*   **Auto-Hide & Fade-Out:** Subtitles automatically fade out and hide after 4–6 seconds of silence, restoring screen space when meetings pause or videos end.
*   **Offline Batch File Transcriber:** Drag-and-drop or select any local video/audio file to extract audio and generate standard subtitles (`.srt` or `.vtt`) in English, Target Language, or Dual mode, saved directly next to the original file. Runs 100% offline using PyAV and Whisper.
*   **High Performance local AI:** Uses `faster-whisper` and optimized CTranslate2 translation engines to deliver low-latency overlays using INT8 CPU quantization.

---

## Architecture & Workflow

```
[System Audio / Zoom / Youtube] ──> [WASAPI Loopback Capture]
                                                │
                                                ▼
[Silero VAD (Noise Filter)] ──(If Silence)──> [Idle State: CPU ~0%, Subtitles Hidden]
                                                │
                                      (If Speech Detected)
                                                ▼
[Local Whisper Engine (tiny)] ──> [Real-time Transcribed Text]
                                                │
                                                ▼
[Offline Translator (Meta NLLB-200)] ──> [Real-time Translated Text]
                                                │
                                                ▼
                                    [Transparent Dual-Subtitle GUI]
```

---

## Getting Started

### Prerequisites
*   **Operating System:** Windows 10/11 (WASAPI Loopback audio capture is natively supported).
*   **Python:** Python 3.8 to 3.12 installed.

### Installation

Choose one of the following methods to set up your environment:

*   **Option A: Using the Installer (Recommended for Windows)**
    Simply double-click the `install.bat` file in the project folder. This will automatically verify your Python installation, initialize the virtual environment (`.venv`), and download all dependencies.
    
*   **Option B: Manual Command Line Setup**
    1. Open your terminal in the `PrivaSub` project directory.
    2. Create the virtual environment:
       ```bash
       python -m venv .venv
       ```
    3. Install the dependencies directly:
       ```bash
       .venv\Scripts\pip install -r requirements.txt
       ```

---

## How to Use

### Starting the Application
You can start the application using one of the following methods:

*   **Method 1: Using the Launcher (Recommended for Windows)**
    Simply double-click the `run.bat` file in the project folder (or run `./run.bat` in your terminal). This runs the application silently in the background (using `pythonw.exe`) without showing any black console window.
    
*   **Method 2: Run directly using the virtual environment**
    In your terminal, run:
    ```bash
    .venv\Scripts\python src/main.py
    ```
    
*   **Method 3: Activate the virtual environment first**
    In your terminal, run:
    ```powershell
    .venv\Scripts\Activate.ps1
    python src/main.py
    ```

### Running Automated Tests

You can run the tests using one of the following commands depending on what you want to verify:

*   **Run the entire test suite** (both unit and integration tests):
    ```bash
    python run_tests.py
    ```
    
*   **Run the integration tests specifically**:
    To run the end-to-end integration tests that verify real-time speech transcription and translation on local video files, run:
    ```bash
    .venv\Scripts\python -m unittest tests.integration.test_integration -v
    ```
    *(If your virtual environment is already activated, you can simply run `python -m unittest tests.integration.test_integration -v`)*.

### Viewing Documentation Locally (VitePress)

PrivaSub includes a fully interactive, beautiful local documentation portal built with VitePress. You can easily spin up the documentation server locally using `npx` (requires Node.js):
```bash
npx vitepress dev docs
```
Once started, open `http://localhost:5173` in your web browser to explore detailed architecture breakdowns, user guides, configuration specs, and feature explanations.

> [!NOTE]
> On your first run, the app will automatically download the optimized `tiny` Whisper multilingual transcription model (~75MB) and the Meta `nllb-200-distilled-600M-ct2-int8` translation model (~600MB) from Hugging Face and cache them locally. Please allow a few minutes for the models to load.

### Interacting with the Subtitles
1. **Locate the Tray Icon:** A blue-and-white subtitle icon will appear in your Windows System Tray (bottom-right taskbar).
2. **Move/Position Overlay:** Right-click the Tray Icon and check **Toggle Draggable (Unlock)**. A border will appear, allowing you to drag the subtitle bar anywhere on the screen. Uncheck it to lock the position.
3. **Lock (Click-Through):** When the window is locked (Toggle Draggable is unchecked), you can click directly "through" the subtitle text onto video players, Zoom controls, or window buttons behind it.
4. **Pause/Resume:** Right-click the Tray Icon and select **Pause Listening** to pause audio capturing and save CPU resources. Select it again to resume.
5. **Batch File Transcriber:** Right-click the Tray Icon and select **Open File Transcriber** to open the Batch File Transcriber window. Drag and drop any video/audio file, configure your output subtitle preferences (English, Target Language, or Dual) and format (SRT or VTT), and click **Start Transcribing & Export**.

### Stopping the Application
To shut down the application completely:
1. Right-click the **PrivaSub** icon in your System Tray.
2. Click **Exit**.
This will cleanly stop all background audio recording streams, close the GUI window, release system memory, and terminate the Python process.

---

## Troubleshooting & Audio Selection Guide

### How to Select the Correct Audio Source
Windows lists multiple sound devices, virtual cables, and hardware outputs. If PrivaSub does not appear to detect audio, follow these rules to pick the right device from the **Audio Source** menu in the System Tray:

1. **Capturing System Audio (Zoom, Teams, YouTube, Browser):**
   * Select a device with the `[Loopback]` prefix.
   * **Listening via Laptop/Desktop Speakers:** Choose `[Loopback] Speakers (Realtek(R) Audio)` or your primary monitor output.
   * **Listening via Headset / AirPods / Bluetooth:** Choose `[Loopback] Headset Earphone` or `[Loopback] Headphones`. *Note: If you switch from speakers to headphones during a meeting, make sure to select the corresponding `[Loopback]` device.*

2. **Capturing Your Own Voice (Microphone):**
   * Select a device with the `[Mic]` prefix.
   * **Using Built-in Mic:** Choose `[Mic] Microphone Array (Realtek(R) Audio)`.
   * **Using External Mic / Headset Mic:** Choose `[Mic] Headset Microphone` or your dedicated USB microphone.

### What if Subtitles are Stuck or Unresponsive?
* **Verify Audio Activity:** PrivaSub uses an intelligent **Silero VAD (Voice Activity Detector)** to keep CPU usage near 0%. If the audio contains only background music, silence, or non-speech noise, the transcriber intentionally remains idle.
* **Check Mute/Pause Status:** Ensure you haven't clicked **Pause Listening** in the System Tray menu.
* **Device Exclusivity:** If another application (like a DAW or specialized audio tool) takes exclusive control of your audio driver, right-click the System Tray icon and select another available audio source to re-establish the connection.

---

## Roadmap

We maintain a public Trello board where you can track our progress, see upcoming features, and vote on cards:
*   **[View our Public Roadmap on Trello](https://trello.com/b/dP5oqzYl/privasub)**

---

## Contributing

Contributions make the open-source community an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project.
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`).
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the Branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

## License

Distributed under the **MIT License**. See `LICENSE` for more information.
