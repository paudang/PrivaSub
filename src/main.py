import sys
import os
import queue
import threading
import time
import pystray
import customtkinter as ctk
from PIL import Image

# Add project root directory to path to support 'src.' imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.ui.live.tray import TrayIconManager
from src.core.hotkey import HotkeyManager
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
        self.is_stealth = self.config.get("stealth_mode", False)
        self.is_disguised = self.config.get("disguised_mode", False)
        self.is_discreet_icon = self.config.get("discreet_tray_icon", False)
        
        # 1. Initialize components
        print("[Main] Initializing PrivaSub components...")
        self.capture = AudioCapture(chunk_duration_ms=100)
        audio_dev_idx = self.config.get("audio_device_index", None)
        if audio_dev_idx is not None:
            self.capture.selected_device_index = audio_dev_idx
        
        # Use tiny.en model for optimized English transcription
        self.transcriber = Transcriber(model_size="tiny.en", device="cpu", compute_type="int8", language="en")
        
        # Initialize offline translator
        print("[Main] Loading offline translator...")
        self.translator = OfflineTranslator(device="cpu", compute_type="int8", source_lang="en", target_lang=self.target_language)
        
        # Initialize UI on main thread
        self.app = SubtitleOverlay()
        self.app.set_click_through(self.is_locked)
        self.app.set_stealth_mode(self.is_stealth)
        self.app.after(100, lambda: self.app.set_stealth_mode(self.is_stealth))
        self.app.set_disguised_mode(self.is_disguised)
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
        self.tray_manager = TrayIconManager(self)
        self.tray_manager.setup_tray()
        
        # 3. Start processing threads
        self.process_thread = threading.Thread(target=self.audio_processing_loop, daemon=True)
        self.process_thread.start()
        
        self.hotkey_manager = HotkeyManager(self)
        self.hotkey_manager.start()
        
        # Start capturing audio
        self.capture.start()
        print("[Main] Ready! App minimized to System Tray.")

    def get_tray_icon_image(self):
        """Proxy to get_tray_icon_image in tray_manager for test compatibility."""
        return self.tray_manager.get_tray_icon_image()

    @property
    def tray_icon(self):
        """Compatibility property for tests."""
        return self.tray_manager.tray_icon if hasattr(self, 'tray_manager') else None

    @tray_icon.setter
    def tray_icon(self, value):
        """Compatibility property setter for tests."""
        if hasattr(self, 'tray_manager'):
            self.tray_manager.tray_icon = value

    def hotkey_listener_loop(self):
        """Compatibility proxy method for tests."""
        if hasattr(self, 'hotkey_manager'):
            self.hotkey_manager._hotkey_listener_loop()

    def on_panic_hotkey(self):
        """Compatibility proxy method for tests."""
        if hasattr(self, 'hotkey_manager'):
            self.hotkey_manager.on_panic_hotkey()

    def on_select_audio_device(self, dev_index, dev_name):
        print(f"[Main] Selecting audio device: {dev_name} (Index: {dev_index})")
        self.capture.set_device(dev_index)
        self.config["audio_device_index"] = dev_index
        AppConfig.save(self.config)
        self.app.after(0, self.app.set_text, f"PrivaSub: Switched audio source to {dev_name}", "", True)
        # Avoid calling update_menu on Windows pystray to prevent tray icon crash/vanish
 
    def on_toggle_lock(self, icon, item):
        """Callback to switch overlay between Click-Through (locked) and Draggable (unlocked)."""
        self.is_locked = not self.is_locked
        self.app.after(0, self.app.set_click_through, self.is_locked)
        # Update text info
        status = "Locked (Click-Through)" if self.is_locked else "Unlocked (Draggable)"
        print(f"[Main] UI status toggled: {status}")
        self.app.after(0, self.app.set_text, f"Captions Overlay: {status}", "", True)

    def on_toggle_stealth(self, icon, item):
        self.is_stealth = not self.is_stealth
        self.app.after(0, self.app.set_stealth_mode, self.is_stealth)
        status = "Enabled (Invisible to Share Screen)" if self.is_stealth else "Disabled"
        print(f"[Main] Stealth Mode toggled: {status}")
        self.app.after(0, self.app.set_text, f"Stealth Mode: {status}", "", True)

    def on_toggle_disguised(self, icon, item):
        self.is_disguised = not self.is_disguised
        self.app.after(0, self.app.set_disguised_mode, self.is_disguised)
        status = "Enabled (Disguised as Notepad)" if self.is_disguised else "Disabled"
        print(f"[Main] Disguised Mode toggled: {status}")
        self.app.after(0, self.app.set_text, f"Disguised Mode: {status}", "", True)

    def on_toggle_discreet_icon(self, icon, item):
        self.is_discreet_icon = not self.is_discreet_icon
        self.tray_manager.update_icon()
        print(f"[Main] Discreet Tray Icon Mode: {self.is_discreet_icon}")

    def on_toggle_pause(self, icon, item):
        """Pauses or resumes audio capturing and transcription."""
        self.is_paused = not self.is_paused
        if self.is_paused:
            print("[Main] Pausing...")
            self.capture.pause()
            # Flush and finalize any remaining text before pausing
            final_text = self.transcriber.finalize()
            if final_text:
                if not final_text[0].isupper():
                    final_text = final_text[0].upper() + final_text[1:]
                trans_text = ""
                if self.target_language != "None" and self.target_language != "None (English Only)":
                    trans_text = self.translator.translate(final_text)
                self.app.after(0, self.app.set_text, final_text, trans_text, True)
            self.app.after(100, self.app.set_text, "PrivaSub: Paused", "", True)
        else:
            print("[Main] Resuming...")
            self.capture.resume()
            self.app.after(0, self.app.set_text, "PrivaSub: Resuming...", "", True)

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
            self.is_stealth = new_config.get("stealth_mode", False)
            self.is_disguised = new_config.get("disguised_mode", False)
            self.is_discreet_icon = new_config.get("discreet_tray_icon", False)
            
            self.transcriber.set_language("en")
            
            if self.target_language != "None" and self.target_language != "None (English Only)":
                self.translator.set_translation_direction("en", self.target_language)
                
            self.app.apply_config(new_config)
            self.app.set_stealth_mode(self.is_stealth)
            self.app.after(100, lambda: self.app.set_stealth_mode(self.is_stealth))
            self.app.set_disguised_mode(self.is_disguised)
            
            self.tray_manager.update_icon()
            
        self.settings_win = SettingsWindow(parent_app=self, on_save_callback=on_settings_saved)

    def _process_and_update(self, chunk):
        """Helper to run transcription/translation on a chunk and post UI updates."""
        res = self.transcriber.process_audio(chunk)
        if res:
            text, is_final = res
            
            # Capitalize first letter of English for display
            if text and not text[0].isupper():
                text = text[0].upper() + text[1:]
                
            # Translate offline only when the segment is finalized (is_final is True)
            # to maximize NLLB-200 translation accuracy and reduce CPU usage.
            trans_text = ""
            if self.target_language != "None" and self.target_language != "None (English Only)":
                if is_final:
                    trans_text = self.translator.translate(text)
                    
            # Push UI update task to Tkinter main thread loop safely
            try:
                self.app.after(0, self.app.set_text, text, trans_text, is_final)
            except Exception:
                pass

    def audio_processing_loop(self):
        """Background thread loop that pulls audio from the queue and feeds it to Whisper."""
        audio_stream_active_notified = False
        import numpy as np
        
        accumulated_chunks = []
        last_trans_run_time = 0.0
        
        while self.running:
            if self.is_paused:
                if accumulated_chunks:
                    combined = np.concatenate(accumulated_chunks)
                    accumulated_chunks = []
                    self._process_and_update(combined)
                time.sleep(0.1)
                continue
                
            # Get processed float32 audio chunk from queue
            chunk = self.capture.get_audio_chunk()
            
            if chunk is not None and len(chunk) > 0:
                accumulated_chunks.append(chunk)
                
                # Check if audio stream has active sound energy
                if not audio_stream_active_notified and np.max(np.abs(chunk)) > 0.001:
                    audio_stream_active_notified = True
                    if hasattr(self.app, 'get_current_text') and self.app.get_current_text() == "PrivaSub loaded. Listening to system audio...":
                        try:
                            self.app.after(0, self.app.set_text, "PrivaSub: Audio stream active, waiting for speech...", "", False)
                        except Exception:
                            pass
            
            # Rate-limit transcription: run only when we have at least 400ms of audio (6400 samples)
            # or if 400ms has elapsed since the last processing run and we have accumulated audio.
            current_time = time.time()
            if accumulated_chunks and (sum(len(c) for c in accumulated_chunks) >= 6400 or (current_time - last_trans_run_time >= 0.4)):
                combined_chunk = np.concatenate(accumulated_chunks)
                accumulated_chunks = []
                self._process_and_update(combined_chunk)
                last_trans_run_time = current_time
                
            if chunk is None:
                time.sleep(0.05)

    def on_exit(self, icon, item):
        """Proper cleanup and exit routine."""
        print("[Main] Cleaning up and exiting...")
        self.running = False
        self.capture.stop()
        
        # Stop System Tray and Hotkey manager
        self.tray_manager.stop()
        self.hotkey_manager.stop()
            
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
