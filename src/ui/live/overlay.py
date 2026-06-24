import sys
import os
import ctypes
import customtkinter as ctk

from src.core.config import AppConfig

class SubtitleOverlay(ctk.CTk):
    def __init__(self, target_alpha=0.8):
        super().__init__()
        
        # Load user config
        self.config = AppConfig.load()
        
        self.target_alpha = self.config.get("opacity", 80) / 100.0
        self.max_history = self.config.get("max_history_lines", 500)
        self.auto_hide_timeout_ms = self.config.get("auto_hide_timeout_s", 15) * 1000
        
        self.is_locked = False
        self.hide_timer_id = None
        self.is_fading = False
        self.fade_steps = 15
        
        # Configure window: borderless, always on top
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", self.target_alpha)
        
        # Default geometry: bottom center of the screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Subtitle window size
        self.win_width = int(screen_width * 0.40)
        self.win_height = 150 # Increased slightly for scrollable history
        self.min_width = self.win_width
        self.min_height = self.win_height
        
        # Position
        x_pos = int((screen_width - self.win_width) / 2)
        y_pos = int(screen_height * 0.85)  # 15% from the bottom
        self.geometry(f"{self.win_width}x{self.win_height}+{x_pos}+{y_pos}")
        
        # Make the background look like a dark translucent pill
        self.configure(fg_color="#121212")
        
        # Add visual components
        self.main_frame = ctk.CTkFrame(
            self,
            fg_color="#1C1C1E",
            corner_radius=12,
            border_width=1,
            border_color="#2C2C2E"
        )
        self.main_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Scrollable Textbox
        self.textbox = ctk.CTkTextbox(
            self.main_frame,
            font=ctk.CTkFont(family="Inter", size=18, weight="normal"),
            text_color="#FFFFFF",
            fg_color="transparent",
            wrap="word",
            state="normal"
        )
        self.textbox.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Prevent keyboard input to make it read-only but keep it normal state
        # so touch scrolling and text selection still works flawlessly
        self.textbox.bind("<Key>", lambda e: "break")
        self.textbox.bind("<<Paste>>", lambda e: "break")
        self.textbox.bind("<<Cut>>", lambda e: "break")
        
        # Configure tags for colors
        self.textbox.tag_config("en", foreground="#FFFFFF")
        self.textbox.tag_config("vi", foreground="#FFD60A")

        # Dragging logic (when not locked)
        # We only bind to the main_frame (the 10px border around the text) so that
        # the user can click and drag inside the textbox to select text or touch-scroll.
        self.main_frame.bind("<ButtonPress-1>", self.start_drag)
        self.main_frame.bind("<B1-Motion>", self.drag)
        
        # Resize Handle (Bottom Right)
        self.resize_handle = ctk.CTkFrame(self.main_frame, width=15, height=15, fg_color="transparent", cursor="size_nw_se")
        self.resize_handle.place(relx=1.0, rely=1.0, anchor="se")
        self.resize_handle.bind("<ButtonPress-1>", self.start_resize)
        self.resize_handle.bind("<B1-Motion>", self.do_resize)
        
        # Explicitly handle mouse wheel for scrolling (important for unfocused transparent windows)
        self.bind("<MouseWheel>", self.on_mousewheel)
        self.textbox.bind("<MouseWheel>", self.on_mousewheel)
        
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._win_start_x = 0
        self._win_start_y = 0
        
        self._resize_start_x = 0
        self._resize_start_y = 0
        self._start_width = 0
        self._start_height = 0
        
        # Initially visible, but will hide quickly if no speech
        self.reset_hide_timer()

    def on_mousewheel(self, event):
        if self.is_locked:
            return
        # Windows event.delta is typically +/- 120
        try:
            # Access internal tkinter Text widget to forcefully scroll
            self.textbox._textbox.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception as e:
            pass

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
        
        # Calculate new potential position using absolute mouse movement
        dx = event.x_root - self._drag_start_x
        dy = event.y_root - self._drag_start_y
        
        new_x = self._win_start_x + dx
        new_y = self._win_start_y + dy
        
        # We don't clamp X and Y to 0 or screen_width because it prevents dragging
        # to secondary monitors (which have negative X or X > screen_width).
        
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
        
        # Calculate unconstrained dimensions
        new_width = max(self._start_width + dx, self.min_width)
        new_height = max(self._start_height + dy, self.min_height)
        
        # Constrain dimensions so the window itself isn't larger than a standard screen.
        # We use winfo_screenwidth/height as a sane maximum size.
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
                # Get the window handle (HWND) of the Tkinter window
                hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
                
                # Get current extended style
                GWL_EXSTYLE = -20
                WS_EX_TRANSPARENT = 0x00000020
                WS_EX_LAYERED = 0x00080000
                
                style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                
                if enabled:
                    # Add transparent style
                    new_style = style | WS_EX_TRANSPARENT | WS_EX_LAYERED
                    # Also update UI border to show it's locked (minimalistic)
                    self.main_frame.configure(border_color="#1C1C1E")
                    self.resize_handle.place_forget()
                else:
                    # Remove transparent style
                    new_style = style & ~WS_EX_TRANSPARENT
                    # Highlight border to show it's draggable
                    self.main_frame.configure(border_color="#3A3A3C")
                    self.resize_handle.place(relx=1.0, rely=1.0, anchor="se")
                    
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
            except Exception as e:
                print(f"[UI] Error setting click-through: {e}")
        else:
            print("[UI] Click-through is only supported on Windows.")

    def set_text(self, en_text, vi_text="", is_final=False):
        """Updates subtitle text and manages showing/hiding states."""
        # Cancel current fade animation if active
        self.is_fading = False
        
        # Restore full target transparency and display window
        self.attributes("-alpha", self.target_alpha)
        if not self.winfo_viewable():
            self.deiconify()
            
        # Reset hide timer on new text
        self.reset_hide_timer()
        
        # If there is previous interim text, delete it
        try:
            self.textbox.delete("interim.first", "interim.last")
        except:
            pass
            
        tag = "interim" if not is_final else "final"
        
        # Smart Auto-Scroll check BEFORE inserting
        try:
            # yview()[1] is 1.0 if the scrollbar is exactly at the bottom
            scroll_pos = self.textbox._textbox.yview()
            is_at_bottom = (scroll_pos[1] >= 0.99)
        except Exception:
            is_at_bottom = True
            
        if en_text:
            self.textbox.insert("end", en_text + "\n", ("en", tag))
        if vi_text:
            self.textbox.insert("end", vi_text + "\n", ("vi", tag))
            
        if is_final:
            # Add an extra blank line for separation after a final segment
            self.textbox.insert("end", "\n", "final")
            
        # Manage history limit (max_history defines max lines to keep)
        try:
            current_lines = int(self.textbox.index("end-1c").split('.')[0])
            max_lines = self.max_history
            if current_lines > max_lines:
                lines_to_delete = current_lines - max_lines
                self.textbox.delete("1.0", f"{lines_to_delete + 1}.0")
        except Exception as e:
            print(f"[UI] Error pruning history: {e}")

        # Only auto-scroll to the bottom if the user was already at the bottom
        if is_at_bottom:
            self.textbox.see("end")
        
        # Handle auto-hide timers
        if self.hide_timer_id:
            self.after_cancel(self.hide_timer_id)
            self.hide_timer_id = None
            
        if is_final:
            self.hide_timer_id = self.after(self.auto_hide_timeout_ms, self.start_fade)
        else:
            # Interim phrase can stick around slightly longer if user stops speaking mid-sentence
            self.hide_timer_id = self.after(self.auto_hide_timeout_ms + 2000, self.start_fade)

    def start_fade(self):
        """Starts the fade-out animation."""
        if self.is_fading:
            return
        self.is_fading = True
        self._fade_step(self.target_alpha, 0.0, self.fade_steps)

    def _fade_step(self, start_alpha, end_alpha, steps_remaining):
        if not self.is_fading:
            # Animation was cancelled (new text arrived)
            return
            
        if steps_remaining <= 0:
            self.attributes("-alpha", end_alpha)
            self.withdraw()  # Hide window completely
            self.is_fading = False
            self.hide_timer_id = None
            return
            
        next_alpha = start_alpha - (start_alpha - end_alpha) / steps_remaining
        self.attributes("-alpha", next_alpha)
        
        # Next step in 40ms (~25 FPS animation)
        self.after(40, self._fade_step, next_alpha, end_alpha, steps_remaining - 1)

    def reset_hide_timer(self):
        """Starts/Resets the timer to hide the UI on startup or reset."""
        if self.hide_timer_id:
            self.after_cancel(self.hide_timer_id)
        self.hide_timer_id = self.after(self.auto_hide_timeout_ms, self.start_fade)
        
    def apply_config(self, new_config):
        self.config = new_config
        self.target_alpha = self.config.get("opacity", 80) / 100.0
        self.max_history = self.config.get("max_history_lines", 500)
        self.auto_hide_timeout_ms = self.config.get("auto_hide_timeout_s", 15) * 1000
        
        # Apply opacity immediately if visible
        if self.winfo_viewable() and not self.is_fading:
            self.attributes("-alpha", self.target_alpha)
            
        # Apply translation height update
        curr_target = self.config.get("target_language", "Vietnamese")
        show_trans = (curr_target != "None" and curr_target != "None (English Only)")
        self.set_translation_visible(show_trans)
        
    def set_translation_visible(self, visible):
        """Toggles the visibility of the Vietnamese translation (updates logic for new segments)."""
        # Since we use a textbox, we don't strictly hide the widget anymore.
        # We just adjust the height if desired, or let the user see more history.
        if visible:
            self.min_height = 150
        else:
            self.min_height = 110
            
        # Update geometry preserving current position
        x_pos = self.winfo_x()
        y_pos = self.winfo_y()
        # If current height is smaller than new min_height, increase it
        curr_height = max(self.winfo_height(), self.min_height)
        curr_width = max(self.winfo_width(), self.min_width)
        self.geometry(f"{curr_width}x{curr_height}+{x_pos}+{y_pos}")

    def close(self):
        """Cleans up timers and destroys window."""
        if self.hide_timer_id:
            self.after_cancel(self.hide_timer_id)
        self.destroy()

if __name__ == "__main__":
    # Test script for UI layout and drag/lock capabilities
    print("Testing Subtitle Overlay UI. Drag it around. In 4 seconds it will lock/enable click-through.")
    app = SubtitleOverlay()
    app.set_text("This is a draggable subtitle test chunk.", "Đây là phần thử nghiệm phụ đề kéo được.", is_final=False)
    
    # After 4 seconds, lock the window and change text
    def lock_test():
        print("Locking window (click-through enabled) & setting final text...")
        app.set_click_through(True)
        app.set_text("Now I am locked! Try to click through me.", "Bây giờ tôi đã khóa! Hãy thử click xuyên qua tôi.", is_final=True)
        
    app.after(4000, lock_test)
    app.mainloop()
