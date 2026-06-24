import os
import sys
import threading
import logging
import customtkinter as ctk
from tkinter import filedialog, messagebox

# Set up logging
logger = logging.getLogger("PrivaSub.FileTranscriberUI")

# Drag-and-drop capability detection
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    HAS_TKDND = True
except ImportError:
    HAS_TKDND = False

# Import batch processor
try:
    from batch_processor import BatchTranscriber
except ImportError:
    # If run directly as a test/script
    sys.path.append(os.path.dirname(__file__))
    from batch_processor import BatchTranscriber

# Define base class depending on DnD availability
if HAS_TKDND:
    class FileTranscriberBase(ctk.CTkToplevel, TkinterDnD.DnDWrapper):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            try:
                self.TkdndVersion = TkinterDnD._require(self)
                self.tkdnd_active = True
            except Exception as e:
                logger.warning(f"Failed to load TkinterDnD extension: {e}. Falling back to click-to-select.")
                self.tkdnd_active = False
else:
    class FileTranscriberBase(ctk.CTkToplevel):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.tkdnd_active = False

class FileTranscriberWindow(FileTranscriberBase):
    def __init__(self, parent_app=None):
        super().__init__()
        
        self.parent_app = parent_app
        self.selected_file_path = None
        self.is_processing = False
        self.output_sub_file = None
        self.was_realtime_running = False
        
        # Configure window properties
        self.title("PrivaSub - Offline File Transcriber")
        self.geometry("540x520")
        self.resizable(False, False)
        
        # Apply dark premium theme
        self.configure(fg_color="#121212")
        
        # Ensure proper close handling
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Setup UI
        self.setup_ui()
        
        # Center the window relative to screen
        self.center_window()
        
        # Bring to front
        self.lift()
        self.focus_force()

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def setup_ui(self):
        # Header Label
        self.header_label = ctk.CTkLabel(
            self,
            text="Offline File Transcriber & Translator",
            font=ctk.CTkFont(family="Inter", size=20, weight="bold"),
            text_color="#FFFFFF"
        )
        self.header_label.pack(pady=(20, 5))
        
        self.subheader_label = ctk.CTkLabel(
            self,
            text="Generate local subtitles for video and audio files securely.",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color="#8E8E93"
        )
        self.subheader_label.pack(pady=(0, 15))

        # Drag and Drop Frame
        self.drop_frame = ctk.CTkFrame(
            self,
            fg_color="#1C1C1E",
            border_width=2,
            border_color="#2C2C2E",
            corner_radius=12,
            height=140
        )
        self.drop_frame.pack(fill="x", padx=30, pady=10)
        self.drop_frame.pack_propagate(False)

        # Labels inside drop frame
        drop_text = "Drag & Drop video/audio file here\n\n— or —\n\nClick to browse local files" if self.tkdnd_active else "Click to select a local video/audio file"
        self.drop_label = ctk.CTkLabel(
            self.drop_frame,
            text=drop_text,
            font=ctk.CTkFont(family="Inter", size=13),
            text_color="#8E8E93",
            justify="center",
            cursor="hand2"
        )
        self.drop_label.pack(expand=True, fill="both")

        # Bind click to select
        self.drop_frame.bind("<Button-1>", lambda e: self.browse_file())
        self.drop_label.bind("<Button-1>", lambda e: self.browse_file())

        # Register Drop Target if DnD is active
        if self.tkdnd_active:
            self.drop_frame.drop_target_register(DND_FILES)
            self.drop_frame.dnd_bind('<<Drop>>', self.handle_drop)
            self.drop_label.drop_target_register(DND_FILES)
            self.drop_label.dnd_bind('<<Drop>>', self.handle_drop)

        # Selected File Label
        self.file_label = ctk.CTkLabel(
            self,
            text="No file selected",
            font=ctk.CTkFont(family="Inter", size=12, slant="italic"),
            text_color="#8E8E93",
            wraplength=480,
            justify="center"
        )
        self.file_label.pack(pady=5)

        # Options Container Frame
        self.options_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.options_frame.pack(fill="x", padx=30, pady=15)
        
        # Subtitle Mode Option
        self.mode_label = ctk.CTkLabel(
            self.options_frame,
            text="Output Mode:",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color="#FFFFFF"
        )
        self.mode_label.grid(row=0, column=0, sticky="w", padx=(0, 10), pady=5)
        
        self.mode_option = ctk.CTkOptionMenu(
            self.options_frame,
            values=["Dual Subtitles (EN + VI)", "English Only", "Vietnamese Only"],
            fg_color="#1C1C1E",
            button_color="#2C2C2E",
            button_hover_color="#3A3A3C",
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Inter", size=12),
            width=200
        )
        self.mode_option.grid(row=0, column=1, sticky="w", pady=5)
        self.mode_option.set("Dual Subtitles (EN + VI)")

        # Subtitle Format Option
        self.format_label = ctk.CTkLabel(
            self.options_frame,
            text="Subtitle Format:",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color="#FFFFFF"
        )
        self.format_label.grid(row=0, column=2, sticky="w", padx=(30, 10), pady=5)
        
        self.format_option = ctk.CTkOptionMenu(
            self.options_frame,
            values=["SRT (.srt)", "VTT (.vtt)"],
            fg_color="#1C1C1E",
            button_color="#2C2C2E",
            button_hover_color="#3A3A3C",
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Inter", size=12),
            width=100
        )
        self.format_option.grid(row=0, column=3, sticky="w", pady=5)
        self.format_option.set("SRT (.srt)")

        # Progress Section
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=30, pady=5)

        self.status_label = ctk.CTkLabel(
            self.progress_frame,
            text="",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color="#0A84FF"
        )
        self.status_label.pack(anchor="w")

        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            orientation="horizontal",
            progress_color="#0A84FF",
            fg_color="#1C1C1E",
            height=8
        )
        self.progress_bar.pack(fill="x", pady=5)
        self.progress_bar.set(0)

        # Buttons Panel
        self.buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.buttons_frame.pack(fill="x", padx=30, pady=15)

        self.transcribe_btn = ctk.CTkButton(
            self.buttons_frame,
            text="Start Transcribing & Export",
            fg_color="#0A84FF",
            hover_color="#0066CC",
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            height=36,
            command=self.start_transcription
        )
        self.transcribe_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.open_folder_btn = ctk.CTkButton(
            self.buttons_frame,
            text="Open Subtitles Folder",
            fg_color="#34C759",
            hover_color="#28A745",
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            height=36,
            command=self.open_subtitles_folder
        )
        # Open folder button is hidden initially
        # We pack/unpack it dynamically
        self.open_folder_btn.pack_forget()

    def handle_drop(self, event):
        if self.is_processing:
            return
        
        # Clean path returned by Windows dnd
        raw_path = event.data
        cleaned_path = raw_path.strip()
        if cleaned_path.startswith('{') and cleaned_path.endswith('}'):
            cleaned_path = cleaned_path[1:-1]
        cleaned_path = cleaned_path.replace("{", "").replace("}", "")
        cleaned_path = cleaned_path.strip('"\'')
        
        self.select_file(cleaned_path)

    def browse_file(self):
        if self.is_processing:
            return
        
        file_path = filedialog.askopenfilename(
            title="Select Video or Audio File",
            filetypes=[
                ("Media Files", "*.mp4 *.avi *.mkv *.mov *.mp3 *.wav *.m4a *.flac *.ogg *.wma *.webm *.aac"),
                ("All Files", "*.*")
            ]
        )
        if file_path:
            self.select_file(file_path)

    def select_file(self, file_path):
        if not os.path.exists(file_path):
            messagebox.showerror("Error", f"File does not exist: {file_path}")
            return
            
        if os.path.isdir(file_path):
            messagebox.showerror("Error", "Please select a file, not a directory.")
            return

        self.selected_file_path = file_path
        self.output_sub_file = None
        self.open_folder_btn.pack_forget()
        self.transcribe_btn.configure(state="normal", text="Start Transcribing & Export")
        
        # Visual check of file type
        _, ext = os.path.splitext(file_path)
        supported_exts = ['.mp4', '.avi', '.mkv', '.mov', '.mp3', '.wav', '.m4a', '.flac', '.ogg', '.wma', '.webm', '.aac']
        if ext.lower() not in supported_exts:
            messagebox.showwarning("Warning", f"File extension '{ext}' might not be supported. The process will still attempt to decode it using PyAV.")

        # Show relative or absolute path nicely
        display_name = os.path.basename(file_path)
        self.file_label.configure(text=f"Selected: {display_name}", text_color="#FFFFFF")
        self.drop_frame.configure(border_color="#0A84FF")
        self.status_label.configure(text="Ready to transcribe.")
        self.progress_bar.set(0)

    def start_transcription(self):
        if not self.selected_file_path:
            messagebox.showwarning("No File Selected", "Please drag-and-drop or select a file first.")
            return
            
        if self.is_processing:
            return

        # Read configurations
        mode_val = self.mode_option.get()
        if "Dual" in mode_val:
            output_mode = "dual"
        elif "Vietnamese" in mode_val:
            output_mode = "vi"
        else:
            output_mode = "en"

        format_val = self.format_option.get()
        output_format = "vtt" if "VTT" in format_val else "srt"

        # Check if output file already exists to prevent accidental overwrite
        base_path, _ = os.path.splitext(self.selected_file_path)
        output_path = base_path + f".{output_format}"
        if os.path.exists(output_path):
            if not messagebox.askyesno("Overwrite Subtitles?", f"The subtitle file already exists:\n\n{os.path.basename(output_path)}\n\nDo you want to overwrite it?"):
                self.is_processing = False
                return

        # Lock UI
        self.is_processing = True
        self.transcribe_btn.configure(state="disabled", text="Transcribing...")
        self.mode_option.configure(state="disabled")
        self.format_option.configure(state="disabled")
        self.drop_frame.configure(border_color="#2C2C2E")
        self.open_folder_btn.pack_forget()
        
        # If main app is running real-time captions, temporarily pause them to conserve RAM/CPU
        self.was_realtime_running = False
        if self.parent_app and not self.parent_app.is_paused:
            logger.info("Pausing real-time capture during batch transcription")
            self.parent_app.on_toggle_pause(None, None)
            self.was_realtime_running = True

        # Run in separate thread
        thread = threading.Thread(
            target=self.run_batch_process, 
            args=(self.selected_file_path, output_mode, output_format), 
            daemon=True
        )
        thread.start()

    def run_batch_process(self, file_path, output_mode, output_format):
        try:
            # Initialize processor (use settings from parent if available)
            device = "cpu"
            compute_type = "int8"
            model_size = "tiny.en"
            
            if self.parent_app and hasattr(self.parent_app, 'transcriber'):
                model_size = self.parent_app.transcriber.model_size
                device = self.parent_app.transcriber.device
                compute_type = self.parent_app.transcriber.compute_type
                
            processor = BatchTranscriber(model_size=model_size, device=device, compute_type=compute_type)
            
            # Progress callback update
            def progress_callback(percent, status):
                self.after(0, self.update_progress, percent, status)

            result_path = processor.process_file(
                input_path=file_path,
                output_mode=output_mode,
                output_format=output_format,
                progress_callback=progress_callback
            )
            
            if result_path and os.path.exists(result_path):
                self.after(0, self.processing_complete, result_path)
            else:
                self.after(0, self.processing_failed, "Failed to generate subtitle file.")
                
        except Exception as e:
            logger.exception("Error in batch processing thread")
            self.after(0, self.processing_failed, str(e))

    def update_progress(self, percent, status):
        if percent < 0:
            self.status_label.configure(text=status, text_color="#FF453A")
            self.progress_bar.set(0)
        else:
            self.status_label.configure(text=f"{status} ({int(percent)}%)", text_color="#0A84FF")
            self.progress_bar.set(percent / 100.0)

    def processing_complete(self, result_path):
        self.is_processing = False
        self.output_sub_file = result_path
        
        # Unlock UI controls
        self.transcribe_btn.configure(state="normal", text="Start Transcribing & Export")
        self.mode_option.configure(state="normal")
        self.format_option.configure(state="normal")
        self.drop_frame.configure(border_color="#0A84FF")
        
        self.status_label.configure(text="Finished! Subtitles saved successfully.", text_color="#30D158")
        self.progress_bar.set(1.0)
        
        # Restore real-time captions if we paused them
        if self.was_realtime_running and self.parent_app and self.parent_app.is_paused:
            logger.info("Resuming real-time capture after batch transcription completion")
            self.parent_app.on_toggle_pause(None, None)
            self.was_realtime_running = False
        
        # Show Open Folder Button
        self.open_folder_btn.pack(side="right", expand=True, fill="x", padx=(5, 0))
        
        # Prompt user
        filename = os.path.basename(result_path)
        messagebox.showinfo("Success", f"Subtitles exported successfully!\n\nFile: {filename}\nSaved in the same folder as your input file.")

    def processing_failed(self, error_msg):
        self.is_processing = False
        
        # Unlock UI controls
        self.transcribe_btn.configure(state="normal", text="Start Transcribing & Export")
        self.mode_option.configure(state="normal")
        self.format_option.configure(state="normal")
        self.drop_frame.configure(border_color="#FF453A")
        
        self.status_label.configure(text=f"Failed: {error_msg}", text_color="#FF453A")
        self.progress_bar.set(0)
        
        # Restore real-time captions if we paused them
        if self.was_realtime_running and self.parent_app and self.parent_app.is_paused:
            logger.info("Resuming real-time capture after batch transcription failure")
            self.parent_app.on_toggle_pause(None, None)
            self.was_realtime_running = False
        
        messagebox.showerror("Transcription Failed", f"An error occurred during transcription:\n\n{error_msg}")

    def open_subtitles_folder(self):
        if self.output_sub_file and os.path.exists(self.output_sub_file):
            folder = os.path.dirname(self.output_sub_file)
            # Use explorer select to highlight the file on Windows
            if sys.platform == "win32":
                os.system(f'explorer /select,"{os.path.normpath(self.output_sub_file)}"')
            else:
                os.startfile(folder) if hasattr(os, 'startfile') else os.system(f'open "{folder}"')

    def on_close(self):
        if self.is_processing:
            if not messagebox.askyesno("Cancel Processing?", "Transcription is currently running. Are you sure you want to stop and close this window?"):
                return
        
        # Restore real-time captions if we paused them
        if self.was_realtime_running and self.parent_app and self.parent_app.is_paused:
            logger.info("Resuming real-time capture on closing transcriber window")
            self.parent_app.on_toggle_pause(None, None)
            self.was_realtime_running = False
        
        # Remove reference from parent app if set
        if self.parent_app and hasattr(self.parent_app, 'transcriber_win'):
            self.parent_app.transcriber_win = None
            
        self.destroy()

if __name__ == "__main__":
    # Test script to verify the layout and look
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    root = ctk.CTk()
    root.withdraw() # Hide root for testing window
    win = FileTranscriberWindow()
    # Define a mock on_close that exits python
    def mock_close():
        win.destroy()
        root.destroy()
        sys.exit(0)
    win.protocol("WM_DELETE_WINDOW", mock_close)
    root.mainloop()
