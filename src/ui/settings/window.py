import os
import customtkinter as ctk
from src.core.config import AppConfig, DEFAULT_CONFIG

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent_app=None, on_save_callback=None):
        super().__init__()
        
        self.parent_app = parent_app
        self.on_save_callback = on_save_callback
        self.config_data = AppConfig.load()
        
        # Configure window properties
        self.title("PrivaSub - Settings")
        self.geometry("420x750")
        self.minsize(400, 700)
        self.resizable(True, True)
        self.configure(fg_color="#121212")
        
        # Set icon if available
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "assets", "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass
        
        self.setup_ui()
        self.center_window()
        self.lift()
        self.focus_force()

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        
        # Always center relative to the entire screen display
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
            
        self.geometry(f"{width}x{height}+{x}+{y}")

    def setup_ui(self):
        # Header
        self.header_label = ctk.CTkLabel(
            self,
            text="Application Settings",
            font=ctk.CTkFont(family="Inter", size=20, weight="bold"),
            text_color="#FFFFFF"
        )
        self.header_label.pack(pady=(20, 15))

        self.main_frame = ctk.CTkFrame(self, fg_color="#1C1C1E", corner_radius=12)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Configure columns so the slider expands when resizing the window
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=0)

        # 1. Max History Lines
        self._create_label(self.main_frame, "Max Subtitle History Lines", 0)
        self.history_slider = ctk.CTkSlider(self.main_frame, from_=100, to=1000, number_of_steps=90, command=self._update_history_val)
        self.history_slider.grid(row=1, column=0, sticky="ew", padx=20, pady=5)
        self.history_val_label = ctk.CTkLabel(self.main_frame, text="", font=ctk.CTkFont(family="Inter", size=12), text_color="#0A84FF")
        self.history_val_label.grid(row=1, column=1, padx=(0, 20))
        self.history_slider.set(self.config_data.get("max_history_lines", 500))
        self._update_history_val(self.history_slider.get())

        # 2. Auto-Hide Timeout
        self._create_label(self.main_frame, "Auto-Hide Timeout (seconds)", 2)
        self.timeout_slider = ctk.CTkSlider(self.main_frame, from_=5, to=30, number_of_steps=25, command=self._update_timeout_val)
        self.timeout_slider.grid(row=3, column=0, sticky="ew", padx=20, pady=5)
        self.timeout_val_label = ctk.CTkLabel(self.main_frame, text="", font=ctk.CTkFont(family="Inter", size=12), text_color="#0A84FF")
        self.timeout_val_label.grid(row=3, column=1, padx=(0, 20))
        self.timeout_slider.set(self.config_data.get("auto_hide_timeout_s", 15))
        self._update_timeout_val(self.timeout_slider.get())

        # 3. Opacity
        self._create_label(self.main_frame, "Window Opacity (%)", 4)
        self.opacity_slider = ctk.CTkSlider(self.main_frame, from_=20, to=100, number_of_steps=80, command=self._update_opacity_val)
        self.opacity_slider.grid(row=5, column=0, sticky="ew", padx=20, pady=5)
        self.opacity_val_label = ctk.CTkLabel(self.main_frame, text="", font=ctk.CTkFont(family="Inter", size=12), text_color="#0A84FF")
        self.opacity_val_label.grid(row=5, column=1, padx=(0, 20))
        self.opacity_slider.set(self.config_data.get("opacity", 80))
        self._update_opacity_val(self.opacity_slider.get())

        # 4. Source Language
        self._create_label(self.main_frame, "Source Language (Audio)", 6)
        curr_source = self.config_data.get("source_language", "English Only")
        self.source_var = ctk.StringVar(value=curr_source)
        self.source_dropdown = ctk.CTkOptionMenu(
            self.main_frame,
            values=["English (Translate Mode)", "English Only"],
            variable=self.source_var,
            font=ctk.CTkFont(family="Inter", size=13),
            fg_color="#2C2C2E",
            button_color="#3A3A3C",
            button_hover_color="#4A4A4C",
            command=self.on_source_change
        )
        self.source_dropdown.grid(row=7, column=0, columnspan=2, sticky="ew", padx=20, pady=(5, 10))

        # 5. Target Translation Language
        self._create_label(self.main_frame, "Target Language (Translation)", 8)
        curr_target = self.config_data.get("target_language", "None")
        self.target_var = ctk.StringVar(value=curr_target)
        self.target_dropdown = ctk.CTkOptionMenu(
            self.main_frame,
            values=["Vietnamese", "Japanese", "Chinese (Simplified)", "Chinese (Traditional)", "Korean", "Spanish", "French", "German", "Russian", "Thai", "None"],
            variable=self.target_var,
            font=ctk.CTkFont(family="Inter", size=13),
            fg_color="#2C2C2E",
            button_color="#3A3A3C",
            button_hover_color="#4A4A4C"
        )
        self.target_dropdown.grid(row=9, column=0, columnspan=2, sticky="ew", padx=20, pady=(5, 25))

        # Initial check for enabled/disabled state
        self.on_source_change(curr_source)

        # 6. Whisper Model Size
        self._create_label(self.main_frame, "Whisper Model Size", 10)
        curr_model = self.config_data.get("whisper_model", "base.en")
        self.model_var = ctk.StringVar(value=curr_model)
        self.model_dropdown = ctk.CTkOptionMenu(
            self.main_frame,
            values=["tiny.en", "base.en", "small.en"],
            variable=self.model_var,
            font=ctk.CTkFont(family="Inter", size=13),
            fg_color="#2C2C2E",
            button_color="#3A3A3C",
            button_hover_color="#4A4A4C"
        )
        self.model_dropdown.grid(row=11, column=0, columnspan=2, sticky="ew", padx=20, pady=(5, 20))

        # 7. Anonymous Sub
        self._create_label(self.main_frame, "Anonymous Sub", 12)
        
        self.stealth_var = ctk.BooleanVar(value=self.config_data.get("stealth_mode", False))
        self.stealth_switch = ctk.CTkSwitch(
            self.main_frame,
            text="Hide Subtitles during Screen Share",
            variable=self.stealth_var,
            font=ctk.CTkFont(family="Inter", size=13),
            text_color="#FFFFFF",
            progress_color="#0A84FF"
        )
        self.stealth_switch.grid(row=13, column=0, columnspan=2, sticky="w", padx=20, pady=(5, 20))

        # Save Button
        self.save_btn = ctk.CTkButton(
            self,
            text="Save & Apply",
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            fg_color="#0A84FF",
            hover_color="#0066CC",
            height=40,
            command=self.save_and_close
        )
        self.save_btn.pack(fill="x", padx=20, pady=(0, 10))

        # Reset Defaults Button
        self.reset_btn = ctk.CTkButton(
            self,
            text="Reset to Defaults",
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            fg_color="#2C2C2E",
            hover_color="#3A3A3C",
            height=40,
            command=self.reset_defaults
        )
        self.reset_btn.pack(fill="x", padx=20, pady=(0, 20))

    def _create_label(self, parent, text, row):
        lbl = ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(family="Inter", size=13, weight="bold"), text_color="#FFFFFF")
        lbl.grid(row=row, column=0, columnspan=2, sticky="w", padx=20, pady=(20, 5))

    def _update_history_val(self, val):
        self.history_val_label.configure(text=f"{int(val)} lines")

    def _update_timeout_val(self, val):
        self.timeout_val_label.configure(text=f"{int(val)} s")

    def _update_opacity_val(self, val):
        self.opacity_val_label.configure(text=f"{int(val)}%")

    def on_source_change(self, value):
        if value == "English Only":
            self.target_dropdown.configure(state="disabled")
            self.target_var.set("None")
        elif value == "English (Translate Mode)":
            self.target_dropdown.configure(state="normal", values=["Vietnamese", "Japanese", "Chinese (Simplified)", "Chinese (Traditional)", "Korean", "Spanish", "French", "German", "Russian", "Thai"])
            if self.target_var.get() == "None":
                self.target_var.set("Vietnamese")

    def save_and_close(self):
        new_config = {
            "max_history_lines": int(self.history_slider.get()),
            "auto_hide_timeout_s": int(self.timeout_slider.get()),
            "opacity": int(self.opacity_slider.get()),
            "source_language": self.source_var.get(),
            "target_language": self.target_var.get(),
            "whisper_model": self.model_var.get(),
            "stealth_mode": self.stealth_var.get(),
            "disguised_mode": self.config_data.get("disguised_mode", False),
            "discreet_tray_icon": self.config_data.get("discreet_tray_icon", False)
        }
        AppConfig.save(new_config)
        
        if self.on_save_callback:
            self.on_save_callback(new_config)
            
        self.destroy()

    def reset_defaults(self):
        # Update sliders and dropdown visually
        self.history_slider.set(DEFAULT_CONFIG["max_history_lines"])
        self._update_history_val(self.history_slider.get())
        
        self.timeout_slider.set(DEFAULT_CONFIG["auto_hide_timeout_s"])
        self._update_timeout_val(self.timeout_slider.get())
        
        self.opacity_slider.set(DEFAULT_CONFIG["opacity"])
        self._update_opacity_val(self.opacity_slider.get())
        
        self.source_var.set(DEFAULT_CONFIG["source_language"])
        self.on_source_change(DEFAULT_CONFIG["source_language"])
        
        self.stealth_var.set(DEFAULT_CONFIG["stealth_mode"])
        self.model_var.set(DEFAULT_CONFIG["whisper_model"])


