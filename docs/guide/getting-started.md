# Quick Start

Follow these steps to set up and run PrivaSub on your local machine.

## Prerequisites

*   **Operating System:** Windows 10/11 (for native WASAPI loopback support).
*   **Python:** Python 3.8 to 3.12 installed. Check your version with:
    ```bash
    python --version
    ```

---

## Installation

Choose one of the following methods to set up your environment:

### Method A: Using the Installer (Recommended for Windows)
Simply double-click the `install.bat` file in the project folder. This will automatically verify your Python installation, initialize the virtual environment (`.venv`), and download all dependencies.

### Method B: Manual Command Line Setup
1.  **Clone or download the project folder** to your workspace.
2.  **Open your terminal** inside the `PrivaSub` project directory.
3.  **Create a Python Virtual Environment**:
    ```bash
    python -m venv .venv
    ```
    
    > [!IMPORTANT]
    > **Virtual Environment Name & Location:**
    > The virtual environment must be created directly in the project root directory and named exactly `.venv` (resulting in the folder path `PrivaSub\.venv`). The helper launcher `run.bat` relies on this exact relative path (`.venv\Scripts\pythonw.exe`) to execute the application silently.

4.  **Install the dependencies directly:**
    ```bash
    .venv\Scripts\pip install -r requirements.txt
    ```

---

## Starting the Application

There are two ways to start the application:

### Method 1: Silent Background Execution (Recommended)
Double-click `run.bat` in the project folder (or run `./run.bat` in your terminal). 
This launches PrivaSub using `pythonw.exe`, running it silently in the background. No console terminal window will be shown.

### Method 2: Standard Terminal Run
With your virtual environment activated, run:
```bash
python src/main.py
```
*Note: On your very first run, PrivaSub will download the optimized `tiny.en` Whisper model (~75MB) from Hugging Face. This might take a minute depending on your internet connection.*

---

## Stopping the Application

To shut down PrivaSub:
1.  Locate the subtitle icon in your Windows **System Tray** (bottom right taskbar).
2.  Right-click the icon and select **Exit**.

This will cleanly terminate the background audio stream, free up the virtual environment memory, and shut down the Python process.
