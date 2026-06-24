import sys
import os
import ctypes
import customtkinter as ctk

class SubtitleOverlay(ctk.CTk):
    def __init__(self, target_alpha=0.8):
        super().__init__()
        
        self.target_alpha = target_alpha
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
        self.win_width = int(screen_width * 0.6)
        self.win_height = 110
        
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
        
        # English Text Label
        self.en_label = ctk.CTkLabel(
            self.main_frame,
            text="PrivaSub: Captions will appear here...",
            font=ctk.CTkFont(family="Inter", size=18, weight="normal"),
            text_color="#FFFFFF",
            wraplength=self.win_width - 40,
            justify="center"
        )
        self.en_label.pack(expand=True, fill="x", padx=20, pady=(10, 2))

        # Vietnamese Text Label (Sleek iOS Yellow for distinction)
        self.vi_label = ctk.CTkLabel(
            self.main_frame,
            text="Phụ đề dịch sẽ xuất hiện ở đây...",
            font=ctk.CTkFont(family="Inter", size=18, weight="normal"),
            text_color="#FFD60A",
            wraplength=self.win_width - 40,
            justify="center"
        )
        self.vi_label.pack(expand=True, fill="x", padx=20, pady=(2, 10))
        
        # Dragging logic (when not locked)
        self.en_label.bind("<ButtonPress-1>", self.start_drag)
        self.en_label.bind("<B1-Motion>", self.drag)
        self.vi_label.bind("<ButtonPress-1>", self.start_drag)
        self.vi_label.bind("<B1-Motion>", self.drag)
        self.main_frame.bind("<ButtonPress-1>", self.start_drag)
        self.main_frame.bind("<B1-Motion>", self.drag)
        
        self._drag_start_x = 0
        self._drag_start_y = 0
        
        # Initially visible, but will hide quickly if no speech
        self.reset_hide_timer()

    def start_drag(self, event):
        if self.is_locked:
            return
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def drag(self, event):
        if self.is_locked:
            return
        x = self.winfo_x() - self._drag_start_x + event.x
        y = self.winfo_y() - self._drag_start_y + event.y
        self.geometry(f"+{x}+{y}")

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
                else:
                    # Remove transparent style
                    new_style = style & ~WS_EX_TRANSPARENT
                    # Highlight border to show it's draggable
                    self.main_frame.configure(border_color="#3A3A3C")
                    
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
            
        self.en_label.configure(text=en_text)
        self.vi_label.configure(text=vi_text)
        
        # Handle auto-hide timers
        if self.hide_timer_id:
            self.after_cancel(self.hide_timer_id)
            self.hide_timer_id = None
            
        if is_final:
            # Finalized phrase, start counting down 4 seconds to hide
            self.hide_timer_id = self.after(4000, self.start_fade)
        else:
            # Interim phrase, keep it alive, but hide if speaker goes silent for 6 seconds
            self.hide_timer_id = self.after(6000, self.start_fade)

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
        self.hide_timer_id = self.after(3000, self.start_fade)
        
    def set_translation_visible(self, visible):
        """Toggles the visibility of the Vietnamese translation label and adjusts window height."""
        if visible:
            self.win_height = 110
            self.vi_label.pack(expand=True, fill="x", padx=20, pady=(2, 10))
        else:
            self.win_height = 80
            self.vi_label.pack_forget()
            
        # Update geometry preserving current position
        x_pos = self.winfo_x()
        y_pos = self.winfo_y()
        self.geometry(f"{self.win_width}x{self.win_height}+{x_pos}+{y_pos}")

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
