import os
import threading
from PIL import Image, ImageDraw
import pystray

class TrayIconManager:
    def __init__(self, parent_app):
        self.parent_app = parent_app
        self.tray_icon = None

    def get_tray_icon_image(self):
        """Loads custom icon or falls back to programmatic generation."""
        if getattr(self.parent_app, 'is_discreet_icon', False):
            # Discreet mode: create a generic dark icon with a subtle green dot
            image = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
            dc = ImageDraw.Draw(image)
            dc.ellipse([16, 16, 48, 48], fill="#2C2C2E")
            dc.ellipse([28, 28, 36, 36], fill="#30D158")
            return image
            
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "assets", "icon.png")
        if os.path.exists(icon_path):
            try:
                return Image.open(icon_path)
            except Exception as e:
                print(f"[Tray] Failed to load tray icon: {e}")
                
        # Fallback generated icon
        image = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        dc.rounded_rectangle([4, 16, 60, 48], radius=8, fill="#1C1C1E", outline="#0A84FF", width=2)
        dc.rectangle([12, 26, 42, 30], fill="#FFFFFF")
        dc.rectangle([12, 34, 52, 38], fill="#0A84FF")
        return image

    def setup_tray(self):
        """Builds the System Tray interface and menu."""
        audio_menu_items = []
        devices = self.parent_app.capture.get_available_devices()
        
        def make_callback(dev_index, dev_name):
            return lambda icon, item: self.parent_app.on_select_audio_device(dev_index, dev_name)
            
        for dev in devices:
            prefix = "[Loopback] " if dev['is_loopback'] else "[Mic] "
            label = f"{prefix}{dev['name']}"
            audio_menu_items.append(pystray.MenuItem(
                label, 
                make_callback(dev['index'], dev['name']),
                checked=lambda item, idx=dev['index']: self.parent_app.capture.selected_device_index == idx or (self.parent_app.capture.selected_device_index is None and self.parent_app.capture.device_index == idx)
            ))
            
        audio_submenu = pystray.Menu(*audio_menu_items) if audio_menu_items else pystray.Menu(pystray.MenuItem("No devices found", lambda icon, item: None))

        menu = pystray.Menu(
            pystray.MenuItem("Toggle Draggable (Unlock)", self.parent_app.on_toggle_lock, checked=lambda item: not self.parent_app.is_locked),
            pystray.MenuItem("Pause Listening", self.parent_app.on_toggle_pause, checked=lambda item: self.parent_app.is_paused),
            pystray.MenuItem("Audio Source", audio_submenu),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Open File Transcriber", self.parent_app.on_open_transcriber),
            pystray.MenuItem("Settings", self.parent_app.on_open_settings),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Show Caption Bar", self.parent_app.on_show_bar),
            pystray.MenuItem("Exit", self.parent_app.on_exit)
        )
        
        from src.core.config import APP_VERSION
        
        self.tray_icon = pystray.Icon(
            "PrivaSub",
            icon=self.get_tray_icon_image(),
            title=f"Realtek Audio Monitor" if getattr(self.parent_app, 'is_discreet_icon', False) else f"PrivaSub v{APP_VERSION} - Offline Captions",
            menu=menu
        )
        
        # Run pystray in a background thread so it doesn't block the Tkinter main loop
        tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        tray_thread.start()

    def update_icon(self):
        if self.tray_icon:
            from src.core.config import APP_VERSION
            self.tray_icon.icon = self.get_tray_icon_image()
            self.tray_icon.title = "Realtek Audio Monitor" if getattr(self.parent_app, 'is_discreet_icon', False) else f"PrivaSub v{APP_VERSION} - Offline Captions"

    def stop(self):
        if self.tray_icon:
            self.tray_icon.stop()
