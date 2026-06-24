# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-06-24

### Added
- **Multilingual Offline Translation:** Transitioned from single-language translation to comprehensive multilingual support utilizing Meta's NLLB-200 (`nllb-200-distilled-600M`) via `CTranslate2` (`int8` quantization). Supported target languages now include Vietnamese, Japanese, Korean, Chinese, Spanish, French, German, Russian, and Arabic.
- **English-First Accuracy Optimization:** Explicitly configured `faster-whisper` to use the `tiny.en` model (English-only) by default for pristine transcription accuracy, and set `DEFAULT_CONFIG` to `source_language: "English Only"` and `target_language: "None"` to ensure zero translation overhead unless explicitly enabled.
- **Window Centering Utility:** Settings and Batch Transcriber windows now automatically center themselves upon launch across all display sizes and configurations.
- **Enterprise Testing Rigor:** Expanded unit test coverage across system audio capture (`system_audio.py`), main application execution loops, and UI event callbacks to comfortably exceed the 90% pre-push hook threshold.

### Changed
- **Refined Subtitle Overlay Ergonomics:** Reduced subtitle box default width to 40% of screen width to prevent excessively wide text lines, providing a cleaner, more readable visual footprint.
- **UI/UX Menu Cleanup:** Removed the redundant "Toggle Translation" option from the system tray menu, guiding users to select their desired target languages cleanly via the Settings UI.

## [1.0.0] - 2026-06-22

### Added
- **Initial Release:** Launched the core MVP of **PrivaSub** for offline desktop captions.
- **Audio Capture:** Integrated Windows WASAPI Loopback system audio recording via `PyAudioWPatch` supporting downmixing and resample pipelines.
- **Local AI Engine:** Integrated `faster-whisper` (CTranslate2) on CPU utilizing `int8` quantization for optimal memory and speed.
- **VAD Processing:** Leveraged Silero Voice Activity Detection to keep CPU utilization at ~0% when no active speech is playing.
- **Premium GUI Overlay:** Created a borderless, transparent, dark-pill styled CustomTkinter subtitle window.
- **Click-Through:** Implemented Win32 API ctypes injection (`WS_EX_TRANSPARENT`) to allow clicking "through" subtitles.
- **Auto-Hide:** Added auto-fade-out and window withdrawal animations when silence persists for 4-6 seconds.
- **System Tray:** Integrated taskbar runner using `pystray` to lock/unlock, pause, and exit the application.
- **Silent Launcher:** Created `run.bat` using `pythonw.exe` to run the app silently without a black console screen.
