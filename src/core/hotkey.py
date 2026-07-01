import ctypes
import threading
import time

# Windows Virtual Key Codes
VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_MENU = 0x12  # Alt
VK_P = 0x50

class HotkeyManager:
    def __init__(self, parent_app):
        self.parent_app = parent_app
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._hotkey_listener_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def _hotkey_listener_loop(self):
        """Monitors Windows keyboard states for global panic hotkey (Ctrl+Shift+Alt+P)."""
        import sys
        if sys.platform != 'win32':
            return
            
        print("[Hotkey] Global panic hotkey listener started (Ctrl+Shift+Alt+P)")
        while self.running and self.parent_app.running:
            time.sleep(0.1)
            # GetAsyncKeyState checks key state since last call
            if (ctypes.windll.user32.GetAsyncKeyState(VK_CONTROL) & 0x8000 and 
                ctypes.windll.user32.GetAsyncKeyState(VK_SHIFT) & 0x8000 and 
                ctypes.windll.user32.GetAsyncKeyState(VK_MENU) & 0x8000 and 
                ctypes.windll.user32.GetAsyncKeyState(VK_P) & 0x8000):
                
                print("[Hotkey] Panic Hotkey (Ctrl+Shift+Alt+P) detected! Toggling window visibility.")
                self.parent_app.app.after(0, self.on_panic_hotkey)
                time.sleep(1.0) # Debounce delay

    def on_panic_hotkey(self):
        app = self.parent_app.app
        if app.winfo_viewable():
            app.withdraw()
        else:
            app.deiconify()
