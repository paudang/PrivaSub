# PrivaSub - Developer Onboarding & Feature Development Context

> **Onboarding Guide & Context Prompt for New Developers and AI Assistants.** 
> When starting new feature development for PrivaSub, read this guide thoroughly or copy its contents into your AI assistant (Gemini, Claude, ChatGPT, etc.) to establish the architectural background, unit test standards, and code push rules.

---

## 1. Project Overview
**PrivaSub** is a live desktop dual-subtitle application for Windows, designed to operate **100% Offline & Privacy-First**.
- **Input:** Captures system audio (YouTube, Zoom, Teams, VLC, etc.) via the Windows WASAPI Loopback protocol.
- **AI Core:** Runs entirely locally on CPU using `faster-whisper` (tiny.en - INT8 quantization) and `MarianMT` (offline English-to-Vietnamese translation).
- **VAD Processing:** Integrates Silero VAD to keep CPU utilization at ~0% during periods of silence.
- **Graphical User Interface (GUI):** Built with `CustomTkinter`, featuring a sleek, semi-transparent, rounded dark overlay. It supports auto-hiding during silence and a **Click-Through** mode (injecting Win32 API window styles to allow clicking through the subtitles).

---

## 2. Current Codebase Structure
The project enforces a strict modular design, cleanly separating the AI Engine, Audio Processing pipelines, and UI Layer:

```text
PrivaSub/
├── assets/                    # Application icons and branding (icon.ico, icon.png, logo)
├── docs/                      # Official documentation (VitePress powered)
├── models/                    # Local storage directory for AI models (Whisper, MarianMT)
├── prompts/                   # Context prompts and onboarding documentation
├── src/                       # Main source code directory
│   ├── core/                  # Core domain logic
│   │   ├── ai/                # transcriber.py (Whisper), translator.py (MarianMT)
│   │   ├── audio/             # system_audio.py (WASAPI loopback), file_extractor.py
│   │   └── config.py          # AppConfig logic managing config.json & App Version
│   ├── services/              # Orchestration and background services (batch_processor.py)
│   ├── ui/                    # GUI Windows and Overlays (CustomTkinter)
│   │   ├── batch/             # Offline file transcriber window (window.py, dnd_base.py)
│   │   ├── live/              # Floating transparent subtitle bar (overlay.py)
│   │   └── settings/          # Configuration UI (window.py)
│   └── main.py                # Main application entrypoint, managing Threads & System Tray
├── tests/                     # Automated Unit Test suite (test_*.py)
├── .githooks/                 # Custom Git hooks (pre-push verification script)
├── .github/workflows/         # CI/CD pipelines (GitHub Actions for PR CI & Docs deployment)
├── install.bat                # Windows installer script (Python setup, venv, desktop shortcut)
├── run.bat                    # Silent background launcher (pythonw.exe, no console window)
├── run_tests.py               # Master automated unit test runner
└── requirements.txt           # Project library dependencies
```

---

## 3. Unit Test Strategy
PrivaSub maintains rigorous standards for stability and testability. Any codebase modification must preserve or improve the code coverage metrics.

### 3.1. Running Tests Locally
The project uses the standard `unittest` framework combined with `coverage.py`. To execute the test suite locally:
```bash
# 1. Run the entire test suite with coverage tracking
coverage run run_tests.py

# 2. Generate the coverage report and verify the 90% passing threshold
coverage report -m --fail-under=90
```

### 3.2. Essential Guidelines for Testing UI (CustomTkinter)
- **Headless UI Testing:** In UI test files (e.g., `tests/test_ui.py`), always invoke `root.withdraw()` or mock window initialization to prevent physical UI windows from rendering, which causes crashes in headless CI environments (GitHub Actions).
- **Popup Dialogs (Messagebox):** Always use `unittest.mock.patch` to mock all `tkinter.messagebox` calls (`showinfo`, `showerror`, etc.). Unmocked popups will block test execution indefinitely waiting for user interaction.
- **Widget Teardown:** Handle widget destruction carefully in `tearDown()`. Avoid calling `destroy()` twice on a widget that was already destroyed during a test case, which triggers a `_tkinter.TclError`.

---

## 4. Mandatory Code Push & PR Rules

### Rule 1: Minimum 90% Code Coverage Requirement
- The project enforces a strict rule: **Unit test coverage must remain at or above 90%**.
- Every new feature or function added in `src/` must be accompanied by relevant unit test cases in `tests/`.

### Rule 2: Git Pre-Push Hook Enforcement
- A pre-push Git hook (`.githooks/pre-push`) is fully configured.
- When executing `git push`, the script automatically triggers `run_tests.py` and evaluates the `fail-under=90` threshold. If any test fails or coverage drops below 90%, the push is blocked locally.

### Rule 3: GitHub Actions PR CI
- All feature branches targeting `main` must go through a **Pull Request (PR)**.
- Upon creating a PR, GitHub Actions (`pr_ci.yml`) automatically sets up a `windows-latest` environment, installs dependencies, and executes the unit tests and 90% coverage check. If the CI job fails, the PR cannot be merged.

---

## 5. AI Feature Development Prompt Template

> **Instructions for Developers:** When instructing an AI assistant to write code or architect a new feature for PrivaSub, copy the prompt template below and append your specific feature requirements.

```text
You are a Senior AI Tech Lead & Python Software Engineer. Please help me develop a new feature for PrivaSub (a 100% Offline Desktop Captions Overlay application for Windows).

[PROJECT CONTEXT & ARCHITECTURE]:
- PrivaSub captures Windows system audio via WASAPI loopback (pyaudiowpatch), processes VAD via Silero, runs speech-to-text via Faster-Whisper (INT8 CPU), and translates via MarianMT.
- The GUI is built with CustomTkinter, featuring Click-Through capabilities (Win32 API injection) and auto-hiding during silence.
- Key source directories: src/core (business logic), src/services (orchestration), src/ui (interfaces), tests/ (unit tests).

[MANDATORY CODING & TESTING STANDARDS]:
1. All newly generated code must strictly adhere to the existing architectural patterns without breaking decoupled modules.
2. You MUST write comprehensive Unit Tests (inside tests/) for all new logic.
3. Total project Code Coverage must remain >= 90% (enforced via fail-under=90).
4. For UI modifications involving CustomTkinter, test files must mock all messagebox popup functions and use root.withdraw() to prevent hanging in headless CI environments.

[NEW FEATURE REQUIREMENTS]:
{INSERT YOUR SPECIFIC NEW FEATURE REQUIREMENTS HERE}
```
