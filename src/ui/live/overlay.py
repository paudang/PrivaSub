import sys
import os
import ctypes
import customtkinter as ctk

from src.core.config import AppConfig
from src.ui.live.window_manager import WindowManagerMixin
from src.ui.live.animation import AnimationMixin
from src.core.constants import SEMANTIC_BREAK_WORDS

class SubtitleOverlay(ctk.CTk, WindowManagerMixin, AnimationMixin):
    def __init__(self, target_alpha=0.8, parent_app=None):
        super().__init__()
        self.parent_app = parent_app
        
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
        self.win_width = 680
        self.win_height = 180
        self.min_width = 680
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
                spacing1=1,
                spacing2=3,
                spacing3=2
            )
        except Exception:
            pass
        
        # Prevent keyboard input to make it read-only but keep it normal state
        # so touch scrolling and text selection still works flawlessly
        self.textbox.bind("<Key>", lambda e: "break")
        self.textbox.bind("<<Paste>>", lambda e: "break")
        self.textbox.bind("<<Cut>>", lambda e: "break")
        
        # Setup context menu for right-click quick controls (when not locked)
        try:
            import tkinter
            self.context_menu = tkinter.Menu(self, tearoff=0)
            self.context_menu.configure(
                bg="#1C1C1E",
                fg="#FFFFFF",
                activebackground="#0A84FF",
                activeforeground="#FFFFFF",
                font=("Inter", 11)
            )
            self.main_frame.bind("<Button-3>", self.show_context_menu)
            self.textbox.bind("<Button-3>", self.show_context_menu)
            self.textbox._textbox.bind("<Button-3>", self.show_context_menu)
        except Exception as e:
            print(f"[UI] Error initializing context menu: {e}")
        
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
            # Check if the last character is currently visible on screen
            if self.textbox._textbox.bbox("end-1c") is not None:
                return True
            # Fallback: check if the scrollbar is scrolled to at least 95%
            _, y_end = self.textbox._textbox.yview()
            return y_end >= 0.95
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

    def wrap_subtitle_text(self, text, max_chars=40, lang="en"):
        """
        Wraps text into lines of at most max_chars, breaking at semantic boundaries
        to follow professional Big Tech (Netflix, BBC, YouTube) subtitle guidelines.
        """
        if not text or len(text) <= max_chars:
            return text
            
        words = text.split()
        lines = []
        current_line = []
        current_len = 0
        
        # Load break words from global SEMANTIC_BREAK_WORDS configuration
        break_words = SEMANTIC_BREAK_WORDS.get(lang, SEMANTIC_BREAK_WORDS.get("en", set()))
        
        for word in words:
            word_len = len(word)
            if current_len + (1 if current_line else 0) + word_len > max_chars:
                if not current_line:
                    current_line.append(word)
                    current_len = word_len
                else:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                    current_len = word_len
            else:
                # Check if this word is a strong semantic break point and we are already at 60%+ line capacity.
                # If so, break early to keep the line semantically clean.
                word_lower = word.lower().strip(",.?!:;()\"'")
                if word_lower in break_words and current_len >= max_chars * 0.6:
                    if current_line:
                        lines.append(" ".join(current_line))
                    current_line = [word]
                    current_len = word_len
                else:
                    current_line.append(word)
                    current_len += (1 if current_len > 0 else 0) + word_len
                    
        if current_line:
            lines.append(" ".join(current_line))
            
        return "\n".join(lines)

    def smooth_scroll_to_end(self, duration_ms=120, steps=6):
        """Smoothly animates the textbox scroll position to the end over duration_ms to prevent layout jumps."""
        if not self.textbox:
            return
            
        try:
            current_scroll = self.textbox._textbox.yview()
            current_top = current_scroll[0]
            current_bottom = current_scroll[1]
            
            if current_bottom >= 0.99:
                return # Already at or very close to the bottom
                
            visible_range = current_bottom - current_top
            target_top = max(0.0, 1.0 - visible_range)
            
            if target_top <= current_top:
                return
                
            step_size = (target_top - current_top) / steps
            
            def scroll_step(step_idx):
                if step_idx >= steps:
                    try:
                        self.textbox._textbox.yview("moveto", target_top)
                    except Exception:
                        pass
                    return
                    
                next_top = current_top + step_size * (step_idx + 1)
                try:
                    self.textbox._textbox.yview("moveto", next_top)
                    self.after(duration_ms // steps, lambda: scroll_step(step_idx + 1))
                except Exception:
                    pass
                    
            scroll_step(0)
        except Exception:
            # Fallback to instant scroll
            try:
                self.textbox.see("end")
            except Exception:
                pass

    def set_text(self, en_text, vi_text="", is_final=False):
        """Updates subtitle text and manages showing/hiding states with zero-flicker in-place updates."""
        is_system_msg = False
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
            
            # Dynamically calculate max characters based on actual textbox width
            box_width = self.textbox.winfo_width()
            if box_width > 10:
                # Average character width of 10 pixels for size 18 font, with margin padding of 30px
                max_chars = max(30, (box_width - 30) // 10)
            else:
                max_chars = 40
                
            if is_system_msg:
                wrapped_en = en_text
                wrapped_vi = vi_text
            else:
                wrapped_en = self.wrap_subtitle_text(en_text, max_chars=max_chars, lang="en") if en_text else ""
                wrapped_vi = self.wrap_subtitle_text(vi_text, max_chars=max_chars, lang="vi") if vi_text else ""
            
            ranges = self.textbox._textbox.tag_ranges("interim")
            if ranges:
                # Disable yscroll callback to prevent scroll jumping during update
                old_yscroll = None
                try:
                    old_yscroll = self.textbox._textbox.cget("yscrollcommand")
                    self.textbox._textbox.configure(yscrollcommand="")
                except Exception:
                    pass
                    
                try:
                    self.textbox.delete("interim.first", "interim.last")
                    if wrapped_en:
                        self.textbox.insert("end", wrapped_en, (en_tag, interim_tag))
                    if wrapped_vi:
                        self.textbox.insert("end", "\n" + wrapped_vi, (vi_tag, interim_tag))
                except Exception:
                    pass
                    
                # Restore scrolling callbacks
                if old_yscroll:
                    try:
                        self.textbox._textbox.configure(yscrollcommand=old_yscroll)
                    except Exception:
                        pass
            else:
                # First interim update: insert at the end
                if wrapped_en:
                    self.textbox.insert("end", wrapped_en, (en_tag, interim_tag))
                if wrapped_vi:
                    self.textbox.insert("end", "\n" + wrapped_vi, (vi_tag, interim_tag))
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
            
            # Dynamically calculate max characters based on actual textbox width
            box_width = self.textbox.winfo_width()
            if box_width > 10:
                # Average character width of 10 pixels for size 18 font, with margin padding of 30px
                max_chars = max(30, (box_width - 30) // 10)
            else:
                max_chars = 40
                
            if is_system_msg:
                wrapped_en = en_text
                wrapped_vi = vi_text
            else:
                wrapped_en = self.wrap_subtitle_text(en_text, max_chars=max_chars, lang="en") if en_text else ""
                wrapped_vi = self.wrap_subtitle_text(vi_text, max_chars=max_chars, lang="vi") if vi_text else ""
            
            if wrapped_en:
                self.textbox.insert("end", wrapped_en + "\n", en_tag)
            if wrapped_vi:
                self.textbox.insert("end", wrapped_vi + "\n", vi_tag)
                
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
            self.smooth_scroll_to_end()
        
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
            self.min_height = 180
        else:
            self.min_height = 130
            
        # Update geometry preserving current position
        x_pos = self.winfo_x()
        y_pos = self.winfo_y()
        # If current height is smaller than new min_height, increase it
        curr_height = max(self.winfo_height(), self.min_height)
        curr_width = max(self.winfo_width(), self.min_width)
        self.geometry(f"{curr_width}x{curr_height}+{x_pos}+{y_pos}")

    def show_context_menu(self, event):
        """Displays a right-click context menu on the overlay for quick controls."""
        if self.is_locked:
            return
            
        try:
            self.context_menu.delete(0, "end")
            
            parent = self.parent_app
            if parent:
                # 1. Pause/Resume toggle
                status_text = "Resume Captions" if parent.is_paused else "Pause Captions"
                self.context_menu.add_command(label=status_text, command=lambda: parent.on_toggle_pause(None, None))
                
                # 2. Lock option
                self.context_menu.add_command(label="Lock Window (Click-Through)", command=self.lock_from_menu)
                
            self.context_menu.add_command(label="Clear Subtitle History", command=self.clear_history)
            
            if parent:
                self.context_menu.add_separator()
                self.context_menu.add_command(label="Open Settings...", command=lambda: parent.on_open_settings(None, None))
                self.context_menu.add_command(label="Exit", command=lambda: parent.on_exit(None, None))
                
            self.context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"[UI] Error showing context menu: {e}")

    def clear_history(self):
        """Clears all subtitle text currently in the box."""
        try:
            self.textbox.configure(state="normal")
            self.textbox.delete("1.0", "end")
            self.textbox.configure(state="normal") # keep normal for scrolling
            print("[UI] Subtitle history cleared.")
        except Exception as e:
            print(f"[UI] Error clearing history: {e}")

    def lock_from_menu(self):
        """Locks the overlay to be click-through, triggered from the context menu."""
        parent = self.parent_app
        if parent:
            parent.on_toggle_lock(None, None)

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
