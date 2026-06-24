import unittest
from unittest.mock import patch, MagicMock
from tkinter import Event
from importlib import reload
import sys
import builtins

# Mock ctypes before importing ui to avoid Windows-specific errors on other OS
# Create a mock for ctypes if testing on non-Windows
if sys.platform != "win32":
    import ctypes
    ctypes.windll = MagicMock()

import customtkinter as ctk
from src.ui.live.overlay import SubtitleOverlay
from src.ui.settings.window import SettingsWindow
from src.ui.batch.window import FileTranscriberWindow
from src.core.config import DEFAULT_CONFIG
import os

class TestSubtitleOverlay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure we have a root window for Tkinter to avoid errors
        cls.root = ctk.CTk()
        cls.root.withdraw() # Hide main window

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    @patch("src.core.config.AppConfig.load")
    def setUp(self, mock_load):
        mock_load.return_value = DEFAULT_CONFIG.copy()
        self.app = SubtitleOverlay(target_alpha=0)
        self.app.withdraw() # Hide during tests

    def tearDown(self):
        self.app.destroy()

    def test_initial_state(self):
        self.assertIsNotNone(self.app.textbox)
        self.assertEqual(self.app.max_history, 500)

    def test_set_text_final(self):
        # Test inserting final text
        self.app.set_text("Hello", "Xin chào", is_final=True)
        text_content = self.app.textbox.get("1.0", "end-1c")
        self.assertIn("Hello", text_content)
        self.assertIn("Xin chào", text_content)

    def test_set_text_interim(self):
        # Test inserting interim text
        self.app.set_text("Hel", "Xi", is_final=False)
        
        # Test replacing interim text with new interim text
        self.app.set_text("Hello world", "Xin chào thế giới", is_final=False)
        text_content = self.app.textbox.get("1.0", "end-1c")
        
        self.assertNotIn("Hel\n", text_content)
        self.assertIn("Hello world", text_content)
        
        # Finalize
        self.app.set_text("Hello world", "Xin chào thế giới", is_final=True)

    def test_history_limit(self):
        # Lower max history to 7 lines for quick testing
        self.app.max_history = 7
        
        # Insert 3 final segments (which should exceed max_history of 6 lines)
        # Each segment is roughly 3 lines (en + vi + newline)
        self.app.set_text("First", "Mot", is_final=True)
        self.app.set_text("Second", "Hai", is_final=True)
        self.app.set_text("Third", "Ba", is_final=True)
        
        text_content = self.app.textbox.get("1.0", "end-1c")
        
        # "First" should have been pruned because max_history is 6 lines
        # Segment 2 and 3 take 6 lines. Segment 1 is pushed out.
        self.assertNotIn("First", text_content)
        self.assertIn("Second", text_content)
        self.assertIn("Third", text_content)

    def test_drag_and_resize(self):
        mock_event = MagicMock()
        mock_event.x = 10
        mock_event.y = 10
        mock_event.x_root = 100
        mock_event.y_root = 100
        
        # Test drag
        self.app.is_locked = False
        self.app.start_drag(mock_event)
        self.assertEqual(self.app._drag_start_x, 100)
        
        mock_event.x_root = 150
        mock_event.y_root = 150
        self.app.drag(mock_event)
        
        # Test resize
        self.app.start_resize(mock_event)
        self.assertEqual(self.app._resize_start_x, 150)
        
        mock_event.x_root = 200
        mock_event.y_root = 200
        self.app.do_resize(mock_event)

    def test_click_through(self):
        self.app.set_click_through(True)
        self.assertTrue(self.app.is_locked)
        self.app.set_click_through(False)
        self.assertFalse(self.app.is_locked)

    def test_apply_config(self):
        self.app.deiconify() # Ensure it's considered visible for alpha update
        new_config = {"opacity": 50, "auto_hide_timeout_s": 5, "max_history_lines": 100}
        self.app.apply_config(new_config)
        self.assertEqual(self.app.target_alpha, 0.5)
        self.assertEqual(self.app.auto_hide_timeout_ms, 5000)
        self.assertEqual(self.app.max_history, 100)
        
    def test_fade_controls(self):
        self.app.reset_hide_timer()
        self.assertIsNotNone(self.app.hide_timer_id)
        self.app.start_fade()
        
    def test_mousewheel(self):
        mock_event = MagicMock()
        mock_event.delta = 120
        self.app.on_mousewheel(mock_event)
        
    def test_close(self):
        with patch.object(self.app, 'destroy') as mock_destroy:
            self.app.close()
            mock_destroy.assert_called()

class TestAdditionalWindows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ctk.CTk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    @patch("src.core.config.AppConfig.load")
    def test_settings_window(self, mock_load):
        mock_load.return_value = DEFAULT_CONFIG.copy()
        win = SettingsWindow()
        win.withdraw()
        
        # Test config updates
        win.opacity_slider.set(70)
        win._update_opacity_val(70)
        
        # Test reset
        win.reset_defaults()
        
        # Test destroy
        win.destroy()

    @patch("src.core.config.AppConfig.load")
    @patch("tkinter.messagebox.showerror")
    @patch("tkinter.messagebox.showwarning")
    @patch("tkinter.messagebox.showinfo")
    @patch("tkinter.messagebox.askyesno")
    def test_batch_window_actions(self, mock_ask, mock_info, mock_warn, mock_err, mock_load):
        mock_ask.return_value = True
        mock_load.return_value = DEFAULT_CONFIG.copy()
        win = FileTranscriberWindow()
        win.withdraw()
        
        # Test ui setup executed without errors
        self.assertIsNotNone(win.transcribe_btn)
        
        # Test start transcription with no file
        win.start_transcription()
        self.assertTrue(mock_warn.called)
        
        # Test select file that exists (mocking os.path.exists)
        with patch('os.path.exists', return_value=True):
            win.select_file("C:/fake.mp4")
            self.assertEqual(win.selected_file_path, "C:/fake.mp4")
            
            # Start transcription mock threading
            with patch('threading.Thread.start') as mock_thread:
                win.start_transcription()
                mock_thread.assert_called()
        
        # Test select invalid
        with patch('os.path.exists', return_value=False):
            win.select_file("C:/missing.mp4")
            self.assertTrue(mock_err.called)
            
        with patch('os.path.exists', return_value=True):
            with patch('os.path.isdir', return_value=True):
                win.select_file("C:/folder")
                self.assertTrue(mock_err.called)
                
        # Test progress
        win.update_progress(50, "Running")
        self.assertEqual(win.progress_bar.get(), 0.5)
        
        win.update_progress(-1, "Error")
        self.assertEqual(win.progress_bar.get(), 0.0)
        
        # Test complete
        win.processing_complete("C:/fake.srt")
        self.assertEqual(win.progress_bar.get(), 1.0)
        self.assertFalse(win.is_processing)
        
        # Test failed
        win.processing_failed("Failed")
        self.assertEqual(win.progress_bar.get(), 0.0)
        self.assertFalse(win.is_processing)
        # Clean up
        win.on_close()

    @patch("src.ui.batch.window.filedialog.askopenfilename")
    @patch("tkinter.messagebox.showerror")
    @patch("src.core.config.AppConfig.load")
    def test_drop_and_browse(self, mock_load, mock_err, mock_ask):
        mock_load.return_value = DEFAULT_CONFIG.copy()
        win = FileTranscriberWindow()
        win.withdraw()
        
        # Test drop valid
        mock_event = MagicMock()
        mock_event.data = "{C:/fake.mp4}"
        with patch.object(win, 'select_file') as mock_select:
            win.handle_drop(mock_event)
            mock_select.assert_called_with("C:/fake.mp4")
            
        # Test drop invalid
        mock_event.data = ""
        win.handle_drop(mock_event)
            
        # Test browse valid
        mock_ask.return_value = "C:/fake.mp4"
        with patch.object(win, 'select_file') as mock_select:
            win.browse_file()
            mock_select.assert_called_with("C:/fake.mp4")
            
        # Test browse cancel
        mock_ask.return_value = ""
        win.browse_file()
                    
    @patch("src.core.config.AppConfig.load")
    def test_run_batch_process(self, mock_load):
        mock_load.return_value = DEFAULT_CONFIG.copy()
        win = FileTranscriberWindow()
        win.withdraw()
        
        # Mock transcriber
        with patch("src.ui.batch.window.BatchTranscriber") as MockTranscriber:
            instance = MockTranscriber.return_value
            instance.process_file.return_value = "C:/fake.srt"
            
            # Execute
            win.run_batch_process("C:/fake.mp4", "en", "srt")
            
            # Verify transcriber called
            instance.process_file.assert_called()
            
            # Verify failure path
            instance.process_file.side_effect = Exception("Test Error")
            win.run_batch_process("C:/fake.mp4", "en", "srt")
            
        win.on_close()
        
    @patch("src.core.config.AppConfig.load")
    def test_batch_window_parent_app_integration(self, mock_load):
        mock_load.return_value = DEFAULT_CONFIG.copy()
        win = FileTranscriberWindow()
        win.withdraw()
        
        # Test restoring realtime captioning on close
        win.parent_app = MagicMock()
        win.parent_app.is_paused = True
        win.parent_app.transcriber_win = win
        win.was_realtime_running = True
        
        win.on_close()
        win.parent_app.on_toggle_pause.assert_called_with(None, None)
        self.assertIsNone(win.parent_app.transcriber_win)
        
    @patch("src.core.config.AppConfig.load")
    def test_batch_window_processing_failed(self, mock_load):
        mock_load.return_value = DEFAULT_CONFIG.copy()
        win = FileTranscriberWindow()
        win.withdraw()
        
        win.parent_app = MagicMock()
        win.parent_app.is_paused = True
        win.was_realtime_running = True
        
        with patch("tkinter.messagebox.showerror"):
            win.processing_failed("Error")
            
        win.parent_app.on_toggle_pause.assert_called_with(None, None)
        win.on_close()

    def test_dnd_base_fallback(self):
        # Temporarily mock tkinterdnd2 missing
        with patch.dict('sys.modules', {'tkinterdnd2': None}):
            import src.ui.batch.dnd_base
            reload(src.ui.batch.dnd_base)
            base = src.ui.batch.dnd_base.FileTranscriberBase()
            self.assertFalse(base.tkdnd_active)
            base.destroy()
            
        # Reload with original
        reload(src.ui.batch.dnd_base)

if __name__ == "__main__":
    unittest.main()
