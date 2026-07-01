import sys
import ctypes

class WindowManagerMixin:
    def start_drag(self, event):
        if self.is_locked:
            return
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root
        self._win_start_x = self.winfo_x()
        self._win_start_y = self.winfo_y()

    def drag(self, event):
        if self.is_locked:
            return
        dx = event.x_root - self._drag_start_x
        dy = event.y_root - self._drag_start_y
        new_x = self._win_start_x + dx
        new_y = self._win_start_y + dy
        self.geometry(f"+{new_x}+{new_y}")

    def start_resize(self, event):
        if self.is_locked:
            return
        self._resize_start_x = event.x_root
        self._resize_start_y = event.y_root
        self._start_width = self.winfo_width()
        self._start_height = self.winfo_height()

    def do_resize(self, event):
        if self.is_locked:
            return
        dx = event.x_root - self._resize_start_x
        dy = event.y_root - self._resize_start_y
        new_width = max(self._start_width + dx, self.min_width)
        new_height = max(self._start_height + dy, self.min_height)
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        new_width = min(new_width, screen_width)
        new_height = min(new_height, screen_height)
        
        self.geometry(f"{new_width}x{new_height}")

    def set_click_through(self, enabled):
        """Toggles the window click-through property on Windows using Win32 API."""
        self.is_locked = enabled
        if sys.platform == "win32":
            try:
                hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
                GWL_EXSTYLE = -20
                WS_EX_TRANSPARENT = 0x00000020
                WS_EX_LAYERED = 0x00080000
                style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                
                if enabled:
                    new_style = style | WS_EX_TRANSPARENT | WS_EX_LAYERED
                    self.main_frame.configure(border_color="#1C1C1E")
                    self.resize_handle.place_forget()
                    self.drag_handle_tr.place_forget()
                    self.drag_handle_mr.place_forget()
                    self.drag_handle_tl.place_forget()
                    self.drag_handle_ml.place_forget()
                else:
                    new_style = style & ~WS_EX_TRANSPARENT
                    self.main_frame.configure(border_color="#3A3A3C")
                    self.resize_handle.place(relx=1.0, rely=1.0, anchor="se")
                    self.drag_handle_tr.place(relx=1.0, rely=0.0, anchor="ne")
                    self.drag_handle_mr.place(relx=1.0, rely=0.5, anchor="e")
                    self.drag_handle_tl.place(relx=0.0, rely=0.0, anchor="nw")
                    self.drag_handle_ml.place(relx=0.0, rely=0.5, anchor="w")
                    
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
            except Exception as e:
                print(f"[UI] Error setting click-through: {e}")
        else:
            print("[UI] Click-through is only supported on Windows.")

    def set_stealth_mode(self, enabled):
        """Toggles WDA_EXCLUDEFROMCAPTURE (0x00000011) to hide window from screen capture/screen sharing."""
        self.is_stealth = enabled
        if sys.platform == "win32":
            try:
                hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
                root_hwnd = ctypes.windll.user32.GetAncestor(self.winfo_id(), 2) or hwnd
                WDA_NONE = 0x00000000
                WDA_EXCLUDEFROMCAPTURE = 0x00000011
                affinity = WDA_EXCLUDEFROMCAPTURE if enabled else WDA_NONE
                success = ctypes.windll.user32.SetWindowDisplayAffinity(root_hwnd, affinity)
                if not success:
                    ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, affinity)
                print(f"[UI] Stealth Mode set to: {enabled}")
            except Exception as e:
                print(f"[UI] Error setting stealth mode: {e}")
        else:
            print("[UI] Stealth mode is only supported on Windows.")
