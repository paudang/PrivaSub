class AnimationMixin:
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
            try:
                self.textbox.delete("1.0", "end")
            except Exception:
                pass
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
