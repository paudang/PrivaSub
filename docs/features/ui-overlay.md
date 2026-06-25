# The Subtitle Overlay (Popup Sub)

The core UI of PrivaSub is the transparent floating subtitle overlay designed for maximum productivity and minimal eye strain.

## Scrollable History
Unlike traditional subtitles that disappear immediately or replace the previous text, PrivaSub uses a **scrollable text area**. 
* **Top-to-Bottom Flow**: New subtitles appear at the bottom, pushing older subtitles upwards.
* **Scroll Back**: When the overlay is unlocked, you can use your mouse wheel to scroll up and read past subtitles if you missed anything.

## History Limit (Configurable)
To prevent the application from consuming too much memory or becoming sluggish, the overlay automatically prunes old history.
* **Default Limit**: By default, the overlay keeps up to **500 lines** of text.
* Once the limit is reached, the oldest lines at the top are automatically removed.

## Color-Coded Transcripts
For clarity when using the translation feature, the overlay uses distinct colors:
* **English Text**: Displayed in standard White.
* **Vietnamese Translation**: Displayed in a sleek, high-visibility iOS Yellow (`#FFD60A`).

## Click-Through & Always On Top
The overlay is designed to hover over your other applications (like Zoom, Chrome, or VLC).
* **Locked Mode**: When locked, Windows passes all mouse clicks directly *through* the overlay to the applications behind it. It will not interfere with your work.
* **Unlocked Mode**: You can drag the overlay using the dedicated side grab handles (`cursor="hand2"`) to reposition it or scroll the text history.

## Dynamic Auto-Hide
If nobody is speaking for a few seconds, the overlay smoothly fades out and hides itself to keep your screen clean. It instantly reappears the moment speech is detected again.

## Resizable, Multi-Monitor & Text Selection
* **Zoom-like Text Selection**: Click freely inside the subtitle text box to highlight and copy (`Ctrl + C`) live captions on the fly.
* **Dedicated Drag Handles**: Intuitive side handles appear when unlocked to let you move the box effortlessly.
* **Multi-Monitor Support**: PrivaSub intelligently detects multi-monitor environments. When you open any popup window (like Settings or the Batch Transcriber), it will automatically spawn perfectly centered on the specific monitor where you are currently viewing the subtitles.
