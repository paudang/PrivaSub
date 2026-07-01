# System Architecture

This page covers the technical architecture and pipeline behind PrivaSub.

## 1. System Audio Loopback Capture
Standard audio recording libraries only capture input devices like microphones. To capture what the computer is playing (Zoom, YouTube, etc.), PrivaSub uses Windows **WASAPI Loopback** via the `PyAudioWPatch` library.

When the application starts:
1.  It queries Windows for the default audio output device (speakers or headphones).
2.  It finds the corresponding Virtual WASAPI loopback input device.
3.  It opens an input stream at the device's **native sample rate** (typically 48000Hz or 44100Hz) and **native channels** (usually 2 channels, stereo) to prevent sample rate errors.

---

## 2. Resampling & Downmixing Pipeline
Whisper models expect audio input in a specific format: **16000Hz, Mono, 32-bit Float, normalized between -1.0 and 1.0**.

PrivaSub processes incoming raw 16-bit PCM (stereo, 48kHz) buffers in real-time:
1.  **Downmixing:** Averages the left and right audio channels to convert stereo to mono.
2.  **Normalization:** Converts 16-bit signed integer values (`-32768` to `32767`) to 32-bit floats (`-1.0` to `1.0`) by dividing by `32768.0`.
3.  **Resampling:** Uses a pure-numpy linear interpolator to resample the audio from 48000Hz (or native rate) to 16000Hz. This avoids heavy external dependencies like `librosa` or `scipy`.

---

## 3. Voice Activity Detection (VAD)
Running speech-to-text models continuously on CPU consumes significant processing power. To keep CPU utilization at ~0% during silence:
1.  Audio chunks (100ms) are pushed into a thread-safe Queue.
2.  PrivaSub passes the rolling accumulator buffer to **Silero VAD** (integrated into `faster-whisper`).
3.  If Silero VAD detects no speech, the Whisper inference loop is skipped, preventing CPU spikes.

---

## 4. Local Whisper Inference
When VAD detects active speech, the processed audio buffer is passed to `faster-whisper`:
*   **Engine:** Powered by `CTranslate2` (a fast C++ inference engine for Transformer models).
*   **Quantization:** Configured to `int8` on CPU. This reduces the memory usage and execution latency by 4x compared to the standard PyTorch FP32 float execution, making it highly responsive on modern laptop/desktop processors.

---

## 5. Offline Machine Translation
Once English text is transcribed by the Whisper engine, it is passed to the offline translation module:
*   **Model:** Powered by an optimized Meta NLLB-200 neural network (`nllb-200-distilled-600M-ct2-int8`) converted to the `CTranslate2` model format, supporting translation into 10 major global target languages.
*   **Tokenization:** Handled locally using Hugging Face `transformers` and `sentencepiece` (without PyTorch).
*   **Performance:** Uses `int8` quantization to achieve translation speeds under **100ms** per sentence directly on your CPU.
*   **Security:** Runs 100% offline, keeping sensitive transcripts private.

---

## 6. Transparent Dual Subtitle Overlay
Both the original transcript and the translation are pushed to the main thread's GUI:
*   **Scrollable Textbox Layout:** Built with `CustomTkinter` using an optimized always-on-top layout that retains history so users can scroll back to read past subtitles.
*   **Windows Click-Through:** Uses ctypes Win32 window style attributes (`WS_EX_TRANSPARENT` and `WS_EX_LAYERED`) to lock the window and permit clicks to pass directly through the subtitles, avoiding interaction locks.
*   **Dynamic Fade-out:** Monitored by a background timer that triggers a smooth alpha-channel opacity transition to completely hide the window after a short duration of silence.
*(For a full list of UI interactions, see [User Interface Features](../features/ui.md))*

---

## 7. In-Process Audio Extraction & Batch Subtitle Export
For local files (video or audio), PrivaSub avoids spawning background command line tools or requiring external `ffmpeg.exe` binaries:
*   **In-Process PyAV Resampling:** Uses PyAV (Pythonic bindings to FFmpeg libraries) via `av.AudioResampler` to programmatically extract the audio track from the media file, downmix it to mono, and resample it to 16kHz mono `pcm_s16le` format. Because this runs completely in-process, it is fast and fully bypasses Windows WDAC/AppLocker rules blocking external sub-process executions.
*   **Batch Transcription & Exporter:** Coordinated by `BatchTranscriber` to load the local Whisper model, transcribe the entire extracted file, translate segments (if requested) into the selected target language via `OfflineTranslator`, format standard SRT (`HH:MM:SS,mmm`) or VTT (`HH:MM:SS.mmm`) timestamp markers, write the output file to disk next to the original media file, and cleanly erase the temporary WAV data.

---

## 8. Source Code Structure
PrivaSub is organized into feature-specific folders to keep the codebase modular, maintainable, and highly decoupled.

```text
src/
├── main.py                     # Main application entry point & coordinator
├── core/                       # Core Processing & AI Logic
│   ├── audio/                  # Audio I/O
│   │   ├── system_audio.py     # WASAPI Loopback capture for live transcription
│   │   ├── device_manager.py   # WASAPI device listing & default loopback search
│   │   └── file_extractor.py   # PyAV audio track extraction for media files
│   ├── ai/                     # Local AI Models
│   │   ├── transcriber.py      # faster-whisper and VAD integration
│   │   └── translator.py       # CTranslate2 NLLB-200 offline translation
│   └── hotkey.py               # Global panic hotkey manager
├── ui/                         # User Interface components
│   ├── live/                   # Real-time subtitle overlay
│   │   ├── overlay.py          # CustomTkinter overlay with smart auto-scroll
│   │   ├── window_manager.py   # Drag/resize & Click-through styling helpers
│   │   ├── animation.py        # Alpha-channel fade transitions
│   │   └── tray.py             # System tray icon setup & menu manager
│   └── batch/                  # Offline File Transcriber UI
│       ├── window.py           # Main batch transcriber window
│       └── dnd_base.py         # Drag-and-drop wrapper and fallback logic
└── services/                   # Background Services
    └── batch_processor.py      # Batch subtitle extraction, transcription, and export pipeline
```
