# Additional Dashboards

PrivaSub provides dedicated standalone popup windows for configuring your experience and running batch offline jobs.

## The Settings UI
Accessible by right-clicking the System Tray icon. The Settings UI allows you to customize the application on the fly:
* **Max History Lines**: Adjust how many lines of past subtitles to keep in memory.
* **Auto-Hide Timeout**: Configure how many seconds of silence before the overlay gracefully fades out.
* **Opacity**: Adjust the background transparency of the subtitle overlay.
* **Target Language**: Easily switch between English-only or translated subtitles.

## The Batch Transcription UI
The main application window provides an offline dashboard for transcribing existing video or audio files. It features:
* **Drag-and-Drop**: Easily drop media files to be transcribed.
* **Auto Pause/Resume**: If you start a batch job while live captions are running, the live captions will automatically pause to prevent overlapping audio, and resume once the batch is done.
* **File Overwrite Protection**: Warns you before overwriting existing `.srt` or `.vtt` files.
* **Progress Tracking**: Real-time progress bar for long video files.
