import sys
import os
import queue
import threading
import time
from PIL import Image, ImageDraw
import pystray
import customtkinter as ctk

# Add project root directory to path to support 'src.' imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.core.audio.system_audio import AudioCapture
from src.core.ai.transcriber import Transcriber
from src.core.ai.translator import OfflineTranslator
from src.ui.live.overlay import SubtitleOverlay
from src.ui.batch.window import FileTranscriberWindow
from src.ui.settings.window import SettingsWindow
from src.core.config import AppConfig, APP_VERSION

class PrivaSubApp:
    def __init__(self):
        self.running = True
        self.is_paused = False
        self.is_locked = False
        
        # Load user settings
        self.config = AppConfig.load()
        self.source_language = self.config.get("source_language", "English Only")
        self.target_language = self.config.get("target_language", "None")
        
        # 1. Initialize components
        print("[Main] Initializing PrivaSub components...")
        self.capture = AudioCapture(chunk_duration_ms=100)
        
        # Use tiny.en model for optimized English transcription
        self.transcriber = Transcriber(model_size="tiny.en", device="cpu", compute_type="int8", language="en")
        
        # Initialize offline translator
        print("[Main] Loading offline translator...")
        self.translator = OfflineTranslator(device="cpu", compute_type="int8", source_lang="en", target_lang=self.target_language)
        
        # Initialize UI on main thread
        self.app = SubtitleOverlay()
        self.app.set_click_through(self.is_locked)
        self.app.set_text("PrivaSub loaded. Listening to system audio...")
        self.transcriber_win = None
        self.settings_win = None
        
        # Set app icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.app.iconbitmap(icon_path)
            except Exception as e:
                print(f"[Main] Failed to set window icon: {e}")
        
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

    def get_tray_icon_image(self):
        """Loads custom icon or falls back to programmatic generation."""
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icon.png")
        if os.path.exists(icon_path):
            try:
                return Image.open(icon_path)
            except Exception as e:
                print(f"[Main] Failed to load tray icon: {e}")
                
        # Fallback generated icon
        image = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        dc.rounded_rectangle([4, 16, 60, 48], radius=8, fill="#1C1C1E", outline="#0A84FF", width=2)
        dc.rectangle([12, 26, 42, 30], fill="#FFFFFF")
        dc.rectangle([12, 34, 52, 38], fill="#0A84FF")
        return image

    def setup_tray(self):
        """Builds the System Tray interface and menu."""
        menu = pystray.Menu(
            pystray.MenuItem("Toggle Draggable (Unlock)", self.on_toggle_lock, checked=lambda item: not self.is_locked),
            pystray.MenuItem("Pause Listening", self.on_toggle_pause, checked=lambda item: self.is_paused),
            pystray.MenuItem("Toggle Translation", self.on_toggle_translation, checked=lambda item: self.target_language != "None" and self.target_language != "None (English Only)"),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Open File Transcriber", self.on_open_transcriber),
            pystray.MenuItem("Settings", self.on_open_settings),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Show Caption Bar", self.on_show_bar),
            pystray.MenuItem("Exit", self.on_exit)
        )
        
        self.tray_icon = pystray.Icon(
            "PrivaSub",
            icon=self.get_tray_icon_image(),
            title=f"PrivaSub v{APP_VERSION} - Offline Captions",
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
        if self.target_language == "None" or self.target_language == "None (English Only)":
            self.target_language = "Vietnamese"
            self.source_language = "English (Translate Mode)"
        else:
            self.target_language = "None"
            self.source_language = "English Only"
            
        print(f"[Main] Target language toggled: {self.target_language}")
        
        # Save to config
        self.config["source_language"] = self.source_language
        self.config["target_language"] = self.target_language
        AppConfig.save(self.config)
        
        self.transcriber.set_language("en")
        
        if self.target_language != "None":
            self.translator.set_translation_direction("en", self.target_language)
        
        # Update UI layout on main thread
        show_trans = (self.target_language != "None" and self.target_language != "None (English Only)")
        self.app.after(0, self.app.set_translation_visible, show_trans)

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

    def on_open_settings(self, icon, item):
        self.app.after(0, self._show_settings_win)

    def _show_settings_win(self):
        if self.settings_win is not None:
            try:
                if self.settings_win.winfo_exists():
                    self.settings_win.deiconify()
                    self.settings_win.lift()
                    self.settings_win.focus_force()
                    return
            except Exception:
                pass
        
        def on_settings_saved(new_config):
            self.config = new_config
            self.source_language = new_config.get("source_language", "English (Translate Mode)")
            self.target_language = new_config.get("target_language", "Vietnamese")
            
            self.transcriber.set_language("en")
            
            if self.target_language != "None" and self.target_language != "None (English Only)":
                self.translator.set_translation_direction("en", self.target_language)
                
            self.app.apply_config(new_config)
            
        self.settings_win = SettingsWindow(parent_app=self, on_save_callback=on_settings_saved)

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
                        
                    # Translate offline only if a target language is selected
                    trans_text = ""
                    if self.target_language != "None" and self.target_language != "None (English Only)":
                        current_time = time.time()
                        
                        if is_final:
                            # Always translate final segments immediately
                            trans_text = self.translator.translate(text)
                            self.last_translated_text = ""
                            self.cached_vi_text = ""
                        elif text == self.last_translated_text:
                            # Reuse cache if text has not changed
                            trans_text = self.cached_vi_text
                        elif current_time - self.last_translation_time > 0.6:
                            # Rate-limit translations of growing interim text (600ms) to prevent flickering
                            trans_text = self.translator.translate(text)
                            self.last_translation_time = current_time
                            self.last_translated_text = text
                            self.cached_vi_text = trans_text
                        else:
                            # Keep displaying cached text during rate limit interval
                            trans_text = self.cached_vi_text
                            
                    # Push UI update task to Tkinter main thread loop safely
                    self.app.after(0, self.app.set_text, text, trans_text, is_final)
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
    import ctypes
    import sys
    
    if sys.platform == 'win32':
        # Prevent multiple instances using a named mutex
        mutex_name = "Global\\PrivaSub_SingleInstance_Mutex"
        mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
        last_error = ctypes.windll.kernel32.GetLastError()
        
        # ERROR_ALREADY_EXISTS = 183
        if last_error == 183:
            # Tell the user and close this new run
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo("PrivaSub", "PrivaSub is already running!")
            return
            
        # Tell Windows this is a distinct app so the taskbar uses our custom icon instead of Python's
        try:
            myappid = 'privasub.desktop.app.1'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass
            
    app = PrivaSubApp()
    app.run()

if __name__ == "__main__":
    main()
