# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
