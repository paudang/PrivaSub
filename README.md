# PrivaSub
> **Offline, Privacy-First Desktop Captions Overlay**

**PrivaSub** is a lightweight, local, and free desktop utility designed to capture system audio (like Zoom meetings, YouTube videos, Teams calls, or VLC players) and transcribe it in real-time onto a premium, transparent overlay. 

Built with privacy at its core, it runs **100% locally on your computer**—requiring zero cloud connections, zero API keys, and absolutely no internet connection after the initial setup.

> [!IMPORTANT]
> **Language Support:** 
> Currently, the application only supports **English audio input** and generates **English subtitles** (English-to-English transcription). Real-time translation to other languages (such as Vietnamese) is scheduled for the next release (see the **Roadmap** below).

---

## Key Features

*   **System Tray Integration:** Runs silently in your taskbar (System Tray), keeping your workspace clutter-free.
*   **VAD-Powered Low CPU Usage:** Utilizes *Silero Voice Activity Detection (VAD)*. The transcription engine remains idle (consuming ~0% CPU) during silence or music, triggering only when speech is detected.
*   **Transparent Overlay:** A sleek, borderless, semi-transparent dark subtitle bar that floats on top of all windows.
*   **Click-Through (Lock Mode):** Click right through the subtitles to interact with YouTube buttons or Zoom features underneath.
*   **Auto-Hide & Fade-Out:** Subtitles automatically fade out and hide after 4–6 seconds of silence, restoring screen space when meetings pause or videos end.
*   **High Performance local STT:** Uses `faster-whisper` (OpenAI Whisper optimized with CTranslate2) to deliver low-latency transcription using INT8 CPU quantization.

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
[Local Whisper Engine (tiny.en)] ──> [Real-time Subtitle Text]
                                                │
                                                ▼
                                    [Transparent Click-Through GUI]
```

---

## Getting Started

### Prerequisites
*   **Operating System:** Windows 10/11 (WASAPI Loopback audio capture is natively supported).
*   **Python:** Python 3.8 to 3.12 installed.

### Installation

1.  Open your terminal in the `PrivaSub` project directory.
2.  Create and activate a virtual environment:
    ```powershell
    # Create the environment
    python -m venv .venv

    # Activate the environment (Windows PowerShell)
    .venv\Scripts\Activate.ps1
    # Or in Command Prompt:
    .venv\Scripts\activate.bat
    ```
3.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
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

> [!NOTE]
> On your first run, the app will automatically download the optimized `tiny.en` Whisper model (~75MB) and cache it locally. Please allow a minute for the models to load.

### Interacting with the Subtitles
1. **Locate the Tray Icon:** A blue-and-white subtitle icon will appear in your Windows System Tray (bottom-right taskbar).
2. **Move/Position Overlay:** Right-click the Tray Icon and check **Toggle Draggable (Unlock)**. A border will appear, allowing you to drag the subtitle bar anywhere on the screen. Uncheck it to lock the position.
3. **Lock (Click-Through):** When the window is locked (Toggle Draggable is unchecked), you can click directly "through" the subtitle text onto video players, Zoom controls, or window buttons behind it.
4. **Pause/Resume:** Right-click the Tray Icon and select **Pause Listening** to pause audio capturing and save CPU resources. Select it again to resume.

### Stopping the Application
To shut down the application completely:
1. Right-click the **PrivaSub** icon in your System Tray.
2. Click **Exit**.
This will cleanly stop all background audio recording streams, close the GUI window, release system memory, and terminate the Python process.

---

## Roadmap

### Phase 1: Core Features (English STT Overlay) - [Current]
- [x] WASAPI Loopback system audio capture (Windows).
- [x] VAD (Voice Activity Detection) integration to achieve ~0% CPU on silence.
- [x] Transparent, borderless click-through overlay subtitles.
- [x] System Tray background execution with pause/exit actions.
- [x] Silent background window launcher (`run.bat` with `pythonw.exe`).

### Phase 2: Translation & File Processing - [Q3 2026]
- [ ] **Offline Translation:** Integrate local machine translation models (e.g., MarianMT/Argos Translate) for real-time English-to-Vietnamese translation on the overlay.
- [ ] **File Subtitling:** Drag-and-drop local video/audio files to extract speech offline and export standard `.srt` or `.vtt` subtitle files.

### Phase 3: Cross-Platform & Hardware Optimization - [Q4 2026]
- [ ] **macOS Support:** CoreAudio & virtual loopback integration (e.g., BlackHole).
- [ ] **Apple Silicon Optimization:** Leverage CoreML / MPS (Metal Performance Shaders) to optimize Whisper running on M1/M2/M3 chips for low battery consumption.
- [ ] **Linux Support:** Support PipeWire/PulseAudio loopback.
- [ ] **Mobile Prototype:** Research offline mic-to-text dictation application for iOS & Android.

### Phase 4: Packaging & PR Launch - [Q1 2027]
- [ ] **Standalone Packaging:** Bundle the app into a single `.exe` (Windows) and `.dmg` (macOS) installer containing the base runtime (removing local Python prerequisites).
- [ ] **Developer PR:** Write step-by-step tech articles explaining the architecture on Dev.to, Medium, and Viblo.
- [ ] **Indie Launch:** Publish the project on Product Hunt, Hacker News, and GitHub trending.
- [ ] **Social Media:** Short-form video demos targeting privacy-focused remote workers and software developers.

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
