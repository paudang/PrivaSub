# Configuration & Settings

PrivaSub is designed to run in the background with minimal user interaction. Most settings are controlled through the **System Tray** menu.

## Subtitle Overlay Modes

The subtitle overlay has two main modes: **Unlocked (Draggable)** and **Locked (Click-Through)**.

### Moving the Subtitle Bar (Unlocked)
1.  Right-click the PrivaSub System Tray icon.
2.  Check **Toggle Draggable (Unlock)**.
3.  A gray border will appear around the subtitle bar. Click and drag the subtitle bar to position it anywhere on your screen.

### Locking and Click-Through (Locked)
1.  Once you have positioned the subtitles, right-click the System Tray icon and uncheck **Toggle Draggable (Unlock)**.
2.  The border will disappear. The overlay is now in **Click-Through** mode.
3.  Any mouse click in the area of the subtitles will pass directly "through" the window, allowing you to click YouTube controls, play/pause video players, or click buttons in Zoom meetings without the subtitles blocking you.

---

## Pause / Resume Controls

If you are listening to music, playing games, or in a call where you don't need subtitles, you can pause the capture engine to save CPU cycles:
1.  Right-click the System Tray icon.
2.  Select **Pause Listening**.
3.  The subtitle window will display `PrivaSub: Paused` and stop listening.
4.  Select it again to resume transcribing.

---

## Auto-Hide & Fade-Out

To keep your screen clean, the subtitle overlay automatically manages its own visibility:
*   **Active Transcribing:** The window stays fully visible with your custom opacity (default is `0.8`).
*   **Pause in Speech:** If no new speech is transcribed after 4-6 seconds, the window triggers a smooth fade-out animation.
*   **Hidden State:** Once faded out, the window is hidden (`withdrawn`) so it takes up zero screen space. It will automatically reappear as soon as someone starts speaking again.
