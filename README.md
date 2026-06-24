# PrivaSub
> **Offline, Privacy-First Desktop Captions Overlay**

**PrivaSub** is a lightweight, local, and free desktop utility designed to capture system audio (like Zoom meetings, YouTube videos, Teams calls, or VLC players) and transcribe it in real-time onto a premium, transparent overlay. 

Built with privacy at its core, it runs **100% locally on your computer**—requiring zero cloud connections, zero API keys, and absolutely no internet connection after the initial setup.

> [!IMPORTANT]
> **Language Support:** 
> Currently, the application supports **English audio input** and generates **dual subtitles** in real-time (English transcript on top, Vietnamese translation on the bottom). Both speech recognition and translation run 100% offline.

---

## Key Features

*   **Real-Time Offline Translation:** Translates English audio directly to Vietnamese on-the-fly using an optimized offline MarianMT model.
*   **Dual Subtitle Layout:** Displays both the original English speech and the translated Vietnamese text simultaneously.
*   **System Tray Integration:** Runs silently in your taskbar (System Tray), keeping your workspace clutter-free.
*   **VAD-Powered Low CPU Usage:** Utilizes *Silero Voice Activity Detection (VAD)*. The transcription engine remains idle (consuming ~0% CPU) during silence or music, triggering only when speech is detected.
*   **Transparent Overlay:** A sleek, borderless, semi-transparent dark subtitle bar that floats on top of all windows.
*   **Click-Through (Lock Mode):** Click right through the subtitles to interact with YouTube buttons or Zoom features underneath.
*   **Auto-Hide & Fade-Out:** Subtitles automatically fade out and hide after 4–6 seconds of silence, restoring screen space when meetings pause or videos end.
*   **Offline Batch File Transcriber:** Drag-and-drop or select any local video/audio file to extract audio and generate standard subtitles (`.srt` or `.vtt`) in English, Vietnamese, or Dual mode, saved directly next to the original file. Runs 100% offline using PyAV and Whisper.
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
[Local Whisper Engine (tiny.en)] ──> [Real-time English Text]
                                                │
                                                ▼
[Offline Translator (MarianMT)] ──> [Real-time Vietnamese Text]
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

To execute the entire unit test suite and verify that all local modules (audio extraction, speech recognition, translation, and export formats) are functional, run:
```bash
python run_tests.py
```

> [!NOTE]
> On your first run, the app will automatically download the optimized `tiny.en` Whisper transcription model (~75MB) and the `opus-mt-en-vi-ctranslate2` translation model (~150MB) from Hugging Face and cache them locally. Please allow a couple of minutes for the models to load.

### Interacting with the Subtitles
1. **Locate the Tray Icon:** A blue-and-white subtitle icon will appear in your Windows System Tray (bottom-right taskbar).
2. **Move/Position Overlay:** Right-click the Tray Icon and check **Toggle Draggable (Unlock)**. A border will appear, allowing you to drag the subtitle bar anywhere on the screen. Uncheck it to lock the position.
3. **Lock (Click-Through):** When the window is locked (Toggle Draggable is unchecked), you can click directly "through" the subtitle text onto video players, Zoom controls, or window buttons behind it.
4. **Pause/Resume:** Right-click the Tray Icon and select **Pause Listening** to pause audio capturing and save CPU resources. Select it again to resume.
5. **Batch File Transcriber:** Right-click the Tray Icon and select **Open File Transcriber** to open the Batch File Transcriber window. Drag and drop any video/audio file, configure your output subtitle preferences (English, Vietnamese, or Dual) and format (SRT or VTT), and click **Start Transcribing & Export**.

### Stopping the Application
To shut down the application completely:
1. Right-click the **PrivaSub** icon in your System Tray.
2. Click **Exit**.
This will cleanly stop all background audio recording streams, close the GUI window, release system memory, and terminate the Python process.

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
