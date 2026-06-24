import sys
import os
import queue
import threading
import time
from PIL import Image, ImageDraw
import pystray
import customtkinter as ctk

# Add src directory to path
sys.path.append(os.path.dirname(__file__))

from audio import AudioCapture
from transcriber import Transcriber
from translator import OfflineTranslator
from ui import SubtitleOverlay
from file_transcriber_ui import FileTranscriberWindow

class PrivaSubApp:
    def __init__(self):
        self.running = True
        self.is_paused = False
        self.is_locked = True  # Start locked (click-through) by default as requested
        self.show_translation = True  # Show Vietnamese translation by default
        
        # 1. Initialize components
        print("[Main] Initializing PrivaSub components...")
        self.capture = AudioCapture(chunk_duration_ms=100)
        
        # Use tiny.en model for quick load and low CPU footprint
        self.transcriber = Transcriber(model_size="tiny.en", device="cpu", compute_type="int8")
        
        # Initialize offline translator
        print("[Main] Loading offline translator...")
        self.translator = OfflineTranslator(device="cpu", compute_type="int8")
        
        # Initialize UI on main thread
        self.app = SubtitleOverlay()
        self.app.set_click_through(self.is_locked)
        self.app.set_text("PrivaSub loaded. Listening to system audio...")
        self.transcriber_win = None
        
        # Caching and rate-limiting variables for translations
        self.last_translation_time = 0.0
        self.last_translated_text = ""
        self.cached_vi_text = ""
        
        # 2. Setup System Tray Icon
        self.tray_icon = None
        self.setup_tray()
        
        # 3. Start processing threads
        self.process_thread = threading.Thread(target=self.audio_processing_loop, daemon=True)
        self.process_thread.start()
        
        # Start capturing audio
        self.capture.start()
        print("[Main] Ready! App minimized to System Tray.")

    def create_tray_icon_image(self):
        """Generates a 64x64 pixel subtitle-like icon programmatically using Pillow."""
        image = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        # Draw dark rounded rectangle background
        dc.rounded_rectangle([4, 16, 60, 48], radius=8, fill="#1C1C1E", outline="#0A84FF", width=2)
        # Draw two text subtitle lines
        dc.rectangle([12, 26, 42, 30], fill="#FFFFFF")
        dc.rectangle([12, 34, 52, 38], fill="#0A84FF")
        return image

    def setup_tray(self):
        """Builds the System Tray interface and menu."""
        menu = pystray.Menu(
            pystray.MenuItem("Toggle Draggable (Unlock)", self.on_toggle_lock, checked=lambda item: not self.is_locked),
            pystray.MenuItem("Pause Listening", self.on_toggle_pause, checked=lambda item: self.is_paused),
            pystray.MenuItem("Show Translation (Vietnamese)", self.on_toggle_translation, checked=lambda item: self.show_translation),
            pystray.MenuItem("Open File Transcriber", self.on_open_transcriber),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Show Caption Bar", self.on_show_bar),
            pystray.MenuItem("Exit", self.on_exit)
        )
        
        self.tray_icon = pystray.Icon(
            "PrivaSub",
            icon=self.create_tray_icon_image(),
            title="PrivaSub - Offline Captions",
            menu=menu
        )
        
        # Run pystray in a background thread so it doesn't block the Tkinter main loop
        tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        tray_thread.start()
 
    def on_toggle_lock(self, icon, item):
        """Callback to switch overlay between Click-Through (locked) and Draggable (unlocked)."""
        self.is_locked = not self.is_locked
        self.app.after(0, self.app.set_click_through, self.is_locked)
        # Update text info
        status = "Locked (Click-Through)" if self.is_locked else "Unlocked (Draggable)"
        print(f"[Main] UI status toggled: {status}")
        self.app.after(0, self.app.set_text, f"Captions Overlay: {status}", "", True)

    def on_toggle_pause(self, icon, item):
        """Pauses or resumes audio capturing and transcription."""
        self.is_paused = not self.is_paused
        if self.is_paused:
            print("[Main] Pausing...")
            self.capture.pause()
            self.transcriber.reset_buffer()
            self.app.after(0, self.app.set_text, "PrivaSub: Paused", "", True)
        else:
            print("[Main] Resuming...")
            self.capture.resume()
            self.app.after(0, self.app.set_text, "PrivaSub: Resuming...", "", True)

    def on_toggle_translation(self, icon, item):
        """Toggles the visibility of translation subtitles."""
        self.show_translation = not self.show_translation
        print(f"[Main] Show translation toggled: {self.show_translation}")
        # Update UI layout on main thread
        self.app.after(0, self.app.set_translation_visible, self.show_translation)

    def on_show_bar(self, icon, item):
        """Forcibly shows the caption bar on screen."""
        self.app.after(0, lambda: self.app.deiconify())
        self.app.after(0, self.app.set_text, "PrivaSub active - waiting for audio...", "", True)

    def on_open_transcriber(self, icon, item):
        """Callback to open the batch file transcriber window."""
        self.app.after(0, self._show_transcriber_win)

    def _show_transcriber_win(self):
        if self.transcriber_win is not None:
            try:
                if self.transcriber_win.winfo_exists():
                    self.transcriber_win.deiconify()
                    self.transcriber_win.lift()
                    self.transcriber_win.focus_force()
                    return
            except Exception:
                pass
        self.transcriber_win = FileTranscriberWindow(parent_app=self)

    def audio_processing_loop(self):
        """Background thread loop that pulls audio from the queue and feeds it to Whisper."""
        while self.running:
            if self.is_paused:
                time.sleep(0.1)
                continue
                
            # Get processed float32 audio chunk from queue
            chunk = self.capture.get_audio_chunk()
            
            if chunk is not None and len(chunk) > 0:
                # Transcribe
                res = self.transcriber.process_audio(chunk)
                if res:
                    text, is_final = res
                    
                    # Capitalize first letter of English for display
                    if text and not text[0].isupper():
                        text = text[0].upper() + text[1:]
                        
                    # Translate to Vietnamese offline only if enabled
                    vi_text = ""
                    if self.show_translation:
                        current_time = time.time()
                        
                        if is_final:
                            # Always translate final segments immediately
                            vi_text = self.translator.translate(text)
                            self.last_translated_text = ""
                            self.cached_vi_text = ""
                        elif text == self.last_translated_text:
                            # Reuse cache if text has not changed
                            vi_text = self.cached_vi_text
                        elif current_time - self.last_translation_time > 0.6:
                            # Rate-limit translations of growing interim text (600ms) to prevent flickering
                            vi_text = self.translator.translate(text)
                            self.last_translation_time = current_time
                            self.last_translated_text = text
                            self.cached_vi_text = vi_text
                        else:
                            # Keep displaying cached text during rate limit interval
                            vi_text = self.cached_vi_text
                            
                    # Push UI update task to Tkinter main thread loop safely
                    self.app.after(0, self.app.set_text, text, vi_text, is_final)
            else:
                time.sleep(0.05)

    def on_exit(self, icon, item):
        """Proper cleanup and exit routine."""
        print("[Main] Cleaning up and exiting...")
        self.running = False
        self.capture.stop()
        
        # Stop System Tray
        if self.tray_icon:
            self.tray_icon.stop()
            
        # Stop CustomTkinter UI and any secondary windows
        if self.transcriber_win is not None:
            try:
                if self.transcriber_win.winfo_exists():
                    self.transcriber_win.after(0, self.transcriber_win.destroy)
            except Exception:
                pass
        self.app.after(0, self.app.close)

    def run(self):
        # Start CustomTkinter event loop on the main thread
        try:
            self.app.mainloop()
        except KeyboardInterrupt:
            self.on_exit(None, None)

def main():
    # Hide the default console window on Windows when starting (optional but good for release)
    # We keep it visible for now during testing
    app = PrivaSubApp()
    app.run()

if __name__ == "__main__":
    main()
