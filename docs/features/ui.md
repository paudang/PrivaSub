# User Interface Features

PrivaSub provides an intuitive and unobtrusive user interface designed for maximum productivity and minimal eye strain.

## The Subtitle Overlay (Popup Sub)

The core UI of PrivaSub is the transparent floating subtitle overlay.

### Scrollable History
Unlike traditional subtitles that disappear immediately or replace the previous text, PrivaSub uses a **scrollable text area**. 
* **Top-to-Bottom Flow**: New subtitles appear at the bottom, pushing older subtitles upwards.
* **Scroll Back**: When the overlay is unlocked, you can use your mouse wheel to scroll up and read past subtitles if you missed anything.

### History Limit (Configurable)
To prevent the application from consuming too much memory or becoming sluggish, the overlay automatically prunes old history.
* **Default Limit**: By default, the overlay keeps up to **500 lines** of text.
* Once the limit is reached, the oldest lines at the top are automatically removed.

### Color-Coded Transcripts
For clarity when using the translation feature, the overlay uses distinct colors:
* **English Text**: Displayed in standard White.
* **Vietnamese Translation**: Displayed in a sleek, high-visibility iOS Yellow (`#FFD60A`).

### Click-Through & Always On Top
The overlay is designed to hover over your other applications (like Zoom, Chrome, or VLC).
* **Locked Mode**: When locked, Windows passes all mouse clicks directly *through* the overlay to the applications behind it. It will not interfere with your work.
* **Unlocked Mode**: You can drag the overlay to reposition it or scroll the text history.

### Dynamic Auto-Hide
If nobody is speaking for a few seconds, the overlay smoothly fades out and hides itself to keep your screen clean. It instantly reappears the moment speech is detected again.

### Resizable & Multi-Monitor Support
The overlay is fully resizable by dragging its edges. PrivaSub intelligently detects multi-monitor environments. When you open any popup window (like Settings or the Batch Transcriber), it will automatically spawn perfectly centered on the specific monitor where you are currently viewing the subtitles.

## The Settings UI
Accessible by right-clicking the System Tray icon. The Settings UI allows you to customize the application on the fly:
* **Max History Lines**: Adjust how many lines of past subtitles to keep in memory.
* **Auto-Hide Timeout**: Configure how many seconds of silence before the overlay gracefully fades out.
* **Opacity**: Adjust the background transparency of the subtitle overlay.
* **Target Language**: Easily switch between English-only or translated Vietnamese subtitles.

## The Batch Transcription UI
The main application window provides an offline dashboard for transcribing existing video or audio files. It features:
* **Drag-and-Drop**: Easily drop media files to be transcribed.
* **Auto Pause/Resume**: If you start a batch job while live captions are running, the live captions will automatically pause to prevent overlapping audio, and resume once the batch is done.
* **File Overwrite Protection**: Warns you before overwriting existing `.srt` or `.vtt` files.
* **Progress Tracking**: Real-time progress bar for long video files.
