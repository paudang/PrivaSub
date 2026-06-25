# Anonymous Sub & Privacy Features

PrivaSub is uniquely designed with robust privacy capabilities for sensitive live environments such as remote interviews or proctored calls where screen sharing is required.

## 1. Anonymous Sub (Hide Subtitles during Screen Share)
Using advanced Windows Display Affinity APIs (`WDA_EXCLUDEFROMCAPTURE`), PrivaSub can make the subtitle overlay completely invisible to screen recording and screen sharing applications (Zoom, Google Meet, Teams, OBS, Discord). 
* **How to use**: Open the **Settings** window from the System Tray and toggle on **Hide Subtitles during Screen Share**. The overlay will remain perfectly visible on your monitor but will be completely hidden from anyone viewing your shared screen or full desktop!

## 2. Global Panic Hotkey
* **Global Panic Hotkey**: Press **Ctrl + Shift + Alt + P** anywhere in Windows to instantly hide or restore the subtitle window without needing to click the taskbar.

## 3. Advanced Experimental APIs (Under the Hood)
During Phase 2 exploration, PrivaSub developed several advanced proof-of-concept capabilities accessible via configuration files or underlying Python APIs:
* **Disguised Mini Box Mode**: Capability to render the UI as a plain text window appearing as `Untitled - Notepad`.
* **Discreet Tray Icon Mode**: Capability to change the tray icon to a generic system circle titled `Realtek Audio Monitor`.
* **Per-Application Audio & Meeting Prioritization**: Experimental support and research for isolating audio streams per-application (e.g., exclusively capturing `zoom.exe` while ignoring background YouTube audio) and automatically detecting active meeting calls.
