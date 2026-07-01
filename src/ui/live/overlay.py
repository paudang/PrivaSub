import sys
import os
import ctypes
import customtkinter as ctk

from src.core.config import AppConfig
from src.ui.live.window_manager import WindowManagerMixin
from src.ui.live.animation import AnimationMixin

class SubtitleOverlay(ctk.CTk, WindowManagerMixin, AnimationMixin):
    def __init__(self, target_alpha=0.8):
        super().__init__()
        
        # Load user config
        self.config = AppConfig.load()
        
        self.target_alpha = self.config.get("opacity", 80) / 100.0
        self.max_history = self.config.get("max_history_lines", 500)
        self.auto_hide_timeout_ms = self.config.get("auto_hide_timeout_s", 15) * 1000
        
        self.is_locked = False
        self.is_stealth = False
        self.is_disguised = False
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
        self.win_width = 520
        self.win_height = 150
        self.min_width = 520
        self.min_height = self.win_height
        
        # Position
        x_pos = int((screen_width - self.win_width) / 2)
        y_pos = int(screen_height * 0.85)  # 15% from the bottom
        self.geometry(f"{self.win_width}x{self.win_height}+{x_pos}+{y_pos}")
        
        # Make the background look like a dark translucent pill
        self.configure(fg_color="#121212")
        
        if sys.platform == "win32":
            try:
                self.wm_attributes("-transparentcolor", "#121212")
            except Exception:
                pass
        
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
        
        # Configure typographical line/paragraph spacing for ultimate closed-caption readability
        try:
            self.textbox._textbox.configure(
                spacing1=2,
                spacing2=4,
                spacing3=10
            )
        except Exception:
            pass
        
        # Prevent keyboard input to make it read-only but keep it normal state
        # so touch scrolling and text selection still works flawlessly
        self.textbox.bind("<Key>", lambda e: "break")
        self.textbox.bind("<<Paste>>", lambda e: "break")
        self.textbox.bind("<<Cut>>", lambda e: "break")
        
        # Configure tags for colors and styles (both final and interim)
        self.textbox.tag_config("en", foreground="#F2F2F7")
        self.textbox.tag_config("vi", foreground="#FFD60A")
        self.textbox.tag_config("en_interim", foreground="#8E8E93") # Sleek iOS-style light gray
        self.textbox.tag_config("vi_interim", foreground="#C7A71C") # Faded/dark gold

        # Dragging logic (when not locked)
        self.main_frame.configure(cursor="hand2")
        self.main_frame.bind("<ButtonPress-1>", self.start_drag)
        self.main_frame.bind("<B1-Motion>", self.drag)
        
        # Dedicated Drag Handles on the Right and Left Sides
        self.drag_handle_tr = ctk.CTkFrame(self.main_frame, width=20, height=20, fg_color="transparent", cursor="hand2")
        self.drag_handle_tr.place(relx=1.0, rely=0.0, anchor="ne")
        self.drag_handle_tr.bind("<ButtonPress-1>", self.start_drag)
        self.drag_handle_tr.bind("<B1-Motion>", self.drag)
        
        self.drag_handle_mr = ctk.CTkFrame(self.main_frame, width=20, height=40, fg_color="transparent", cursor="hand2")
        self.drag_handle_mr.place(relx=1.0, rely=0.5, anchor="e")
        self.drag_handle_mr.bind("<ButtonPress-1>", self.start_drag)
        self.drag_handle_mr.bind("<B1-Motion>", self.drag)
        
        self.drag_handle_tl = ctk.CTkFrame(self.main_frame, width=20, height=20, fg_color="transparent", cursor="hand2")
        self.drag_handle_tl.place(relx=0.0, rely=0.0, anchor="nw")
        self.drag_handle_tl.bind("<ButtonPress-1>", self.start_drag)
        self.drag_handle_tl.bind("<B1-Motion>", self.drag)
        
        self.drag_handle_ml = ctk.CTkFrame(self.main_frame, width=20, height=40, fg_color="transparent", cursor="hand2")
        self.drag_handle_ml.place(relx=0.0, rely=0.5, anchor="w")
        self.drag_handle_ml.bind("<ButtonPress-1>", self.start_drag)
        self.drag_handle_ml.bind("<B1-Motion>", self.drag)
        
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
        
        # Cache for currently displayed interim text to avoid redundant updates and flickering
        self.last_en_interim = ""
        self.last_vi_interim = ""

    def is_scrolled_to_bottom(self):
        """Returns True if the scroll position is at the very bottom (with a small margin)."""
        try:
            _, y_end = self.textbox._textbox.yview()
            return y_end >= 0.98
        except Exception:
            return True

    def is_end_visible(self):
        """Returns True if the very end of the text is currently visible on the screen."""
        try:
            return self.textbox._textbox.bbox("end-1c") is not None
        except Exception:
            return True

    def on_mousewheel(self, event):
        if self.is_locked:
            return
        # Windows event.delta is typically +/- 120
        try:
            # Access internal tkinter Text widget to forcefully scroll
            self.textbox._textbox.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception as e:
            pass



    def set_disguised_mode(self, enabled):
        """Toggles Disguised Mini Box mode (looks like plain Notepad) to avoid suspicion."""
        self.is_disguised = enabled
        if enabled:
            self.overrideredirect(False)
            self.title("Untitled - Notepad")
            self.configure(fg_color="#FFFFFF")
            self.main_frame.configure(fg_color="#FFFFFF", border_color="#CCCCCC")
            self.textbox.configure(fg_color="#FFFFFF", text_color="#000000")
            self.textbox.tag_config("en", foreground="#000000")
            self.textbox.tag_config("vi", foreground="#333333")
            self.textbox.tag_config("en_interim", foreground="#555555")
            self.textbox.tag_config("vi_interim", foreground="#666666")
            self.attributes("-alpha", 1.0)
        else:
            self.overrideredirect(True)
            self.configure(fg_color="#121212")
            self.main_frame.configure(fg_color="#1C1C1E", border_color="#2C2C2E")
            self.textbox.configure(fg_color="transparent", text_color="#FFFFFF")
            self.textbox.tag_config("en", foreground="#F2F2F7")
            self.textbox.tag_config("vi", foreground="#FFD60A")
            self.textbox.tag_config("en_interim", foreground="#8E8E93")
            self.textbox.tag_config("vi_interim", foreground="#C7A71C")
            self.attributes("-alpha", self.target_alpha)
        print(f"[UI] Disguised Mode set to: {enabled}")

    def get_current_text(self):
        """Returns the current raw text content of the textbox."""
        try:
            return self.textbox.get("1.0", "end-1c").strip()
        except Exception:
            return ""

    def set_text(self, en_text, vi_text="", is_final=False):
        """Updates subtitle text and manages showing/hiding states with zero-flicker in-place updates."""
        # Strip punctuation for UI display to prevent visual stutter (speech transcription only)
        if en_text:
            is_system_msg = any(en_text.startswith(prefix) for prefix in ["PrivaSub", "Captions Overlay", "Stealth Mode", "Disguised Mode"])
            if not is_system_msg:
                import re
                en_text = re.sub(r'[.,!?;;:]', '', en_text)
                en_text = re.sub(r'\s+', ' ', en_text).strip()
                if vi_text:
                    vi_text = re.sub(r'[.,!?;;:]', '', vi_text)
                    vi_text = re.sub(r'\s+', ' ', vi_text).strip()

        if not en_text and not vi_text:
            return
            
        # Redundant update check to prevent flickering/stuttering on identical updates
        if not is_final:
            if en_text == self.last_en_interim and vi_text == self.last_vi_interim:
                return
            self.last_en_interim = en_text
            self.last_vi_interim = vi_text
        else:
            self.last_en_interim = ""
            self.last_vi_interim = ""

        # Cancel current fade animation if active
        self.is_fading = False
        
        # Restore full target transparency and display window
        alpha_val = 1.0 if self.is_disguised else self.target_alpha
        self.attributes("-alpha", alpha_val)
        if not self.winfo_viewable():
            self.deiconify()
            
        # Check if user is scrolled to the bottom before we modify content
        should_scroll = self.is_scrolled_to_bottom()
        
        # Temporarily disable scrolling callbacks to avoid layout/scrollbar jitter during update
        old_yscroll = None
        try:
            old_yscroll = self.textbox._textbox.cget("yscrollcommand")
            self.textbox._textbox.configure(yscrollcommand="")
        except Exception:
            pass

        # 1. Update text using character-level diffing to prevent visual flickering
        if not is_final:
            interim_tag = "interim"
            en_tag = "en_interim"
            vi_tag = "vi_interim"
            
            # Fall back to delete-and-reinsert if Vietnamese interim text is passed
            # to keep tag styling intact for backwards-compatibility (mostly tests)
            if vi_text:
                try:
                    ranges = self.textbox._textbox.tag_ranges("interim")
                    if ranges:
                        self.textbox.delete("interim.first", "interim.last")
                except Exception:
                    pass
                if en_text:
                    self.textbox.insert("end", en_text, (en_tag, interim_tag))
                if vi_text:
                    self.textbox.insert("end", "\n" + vi_text, (vi_tag, interim_tag))
            else:
                # Normal live mode: only English interim text is present. Use strictly additive suffix alignment.
                ranges = self.textbox._textbox.tag_ranges("interim")
                if ranges:
                    try:
                        # Retrieve currently displayed interim text
                        current_interim = self.textbox._textbox.get("interim.first", "interim.last")
                        
                        # Find the additive suffix to append
                        current_words = current_interim.split()
                        new_words = en_text.split()
                        
                        suffix_to_append = ""
                        if not current_words:
                            suffix_to_append = en_text
                        else:
                            # Search for matching overlap
                            match_found = False
                            for suffix_len in range(min(len(current_words), 4), 0, -1):
                                suffix = current_words[-suffix_len:]
                                for i in range(len(new_words) - suffix_len + 1):
                                    if new_words[i : i + suffix_len] == suffix:
                                        new_suffix_words = new_words[i + suffix_len :]
                                        suffix_to_append = " ".join(new_suffix_words)
                                        match_found = True
                                        break
                                if match_found:
                                    break
                                    
                            if not match_found:
                                # Fallback: append words if new text is longer
                                if len(new_words) > len(current_words):
                                    suffix_to_append = " ".join(new_words[len(current_words) :])
                        
                        if suffix_to_append:
                            # Prepend a space if the interim text doesn't end with whitespace
                            if current_interim and not current_interim[-1].isspace():
                                suffix_to_append = " " + suffix_to_append
                            self.textbox._textbox.insert("interim.last", suffix_to_append, (en_tag, interim_tag))
                    except Exception:
                        # Fallback to delete and insert if index error occurs
                        try:
                            self.textbox.delete("interim.first", "interim.last")
                        except Exception:
                            pass
                        if en_text:
                            self.textbox.insert("end", en_text, (en_tag, interim_tag))
                else:
                    # First interim update: insert at the end
                    if en_text:
                        self.textbox.insert("end", en_text, (en_tag, interim_tag))
        else:
            # Final text: delete interim range first
            try:
                ranges = self.textbox._textbox.tag_ranges("interim")
                if ranges:
                    self.textbox.delete("interim.first", "interim.last")
            except Exception:
                pass
            # Final text: insert English and Vietnamese with proper trailing newlines
            en_tag = "en"
            vi_tag = "vi"
            
            if en_text:
                self.textbox.insert("end", en_text + "\n", en_tag)
            if vi_text:
                self.textbox.insert("end", vi_text + "\n", vi_tag)
                
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

        # Restore scrolling callbacks
        if old_yscroll:
            try:
                self.textbox._textbox.configure(yscrollcommand=old_yscroll)
            except Exception:
                pass

        # 3. Intelligent auto-scrolling
        # Automatically scroll to bottom if the user was already at the bottom.
        if should_scroll:
            try:
                self.textbox.see("end")
                if is_final:
                    self.after(50, lambda: self.textbox.see("end"))
            except Exception:
                pass
        
        # Handle auto-hide timers
        if self.hide_timer_id:
            self.after_cancel(self.hide_timer_id)
            self.hide_timer_id = None
            
        if is_final:
            self.hide_timer_id = self.after(self.auto_hide_timeout_ms, self.start_fade)
        else:
            # Interim phrase can stick around slightly longer if user stops speaking mid-sentence
            self.hide_timer_id = self.after(self.auto_hide_timeout_ms + 2000, self.start_fade)


        
    def apply_config(self, new_config):
        self.config = new_config
        self.target_alpha = self.config.get("opacity", 80) / 100.0
        self.max_history = self.config.get("max_history_lines", 500)
        self.auto_hide_timeout_ms = self.config.get("auto_hide_timeout_s", 15) * 1000
        
        # Apply opacity immediately if visible
        if self.winfo_viewable() and not self.is_fading:
            alpha_val = 1.0 if self.is_disguised else self.target_alpha
            self.attributes("-alpha", alpha_val)
            
        # Apply translation height update
        curr_target = self.config.get("target_language", "Vietnamese")
        show_trans = (curr_target != "None" and curr_target != "None (English Only)")
        self.set_translation_visible(show_trans)
        
    def set_translation_visible(self, visible):
        """Toggles the visibility of the Vietnamese translation (updates logic for new segments)."""
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
