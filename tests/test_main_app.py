import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from src.main import PrivaSubApp, main

class TestMainApp(unittest.TestCase):
    @patch("src.main.AudioCapture")
    @patch("src.main.Transcriber")
    @patch("src.main.OfflineTranslator")
    @patch("src.main.SubtitleOverlay")
    @patch("src.main.pystray")
    @patch("src.main.threading.Thread")
    def test_app_initialization_and_actions(self, mock_thread, mock_pystray, mock_overlay, mock_trans, mock_whisper, mock_cap):
        app = PrivaSubApp()
        self.assertIsNotNone(app)
        
        # Test tray icon image generation fallback
        img = app.get_tray_icon_image()
        self.assertIsNotNone(img)
        
        # Test tray actions
        app.on_toggle_lock(None, None)
        self.assertTrue(app.is_locked)
        
        app.on_toggle_pause(None, None)
        self.assertTrue(app.is_paused)
        
        app.on_toggle_pause(None, None)
        self.assertFalse(app.is_paused)
        
        app.on_show_bar(None, None)
        app.on_open_transcriber(None, None)
        app.on_open_settings(None, None)
        
        # Test new stealth and disguised modes
        app.is_stealth = False
        app.on_toggle_stealth(None, None)
        self.assertTrue(app.is_stealth)
        
        app.is_disguised = False
        app.on_toggle_disguised(None, None)
        self.assertTrue(app.is_disguised)
        
        app.is_discreet_icon = False
        app.on_toggle_discreet_icon(None, None)
        self.assertTrue(app.is_discreet_icon)
        
        # Test get_tray_icon_image under discreet mode
        img_discreet = app.get_tray_icon_image()
        self.assertIsNotNone(img_discreet)
        
        # Test panic hotkey
        app.app.winfo_viewable.return_value = True
        app.on_panic_hotkey()
        app.app.winfo_viewable.return_value = False
        app.on_panic_hotkey()
        
        # Test exit
        app.on_exit(None, None)
        self.assertFalse(app.running)
        
    @patch("src.main.time.sleep")
    @patch("src.main.AudioCapture")
    @patch("src.main.Transcriber")
    @patch("src.main.OfflineTranslator")
    @patch("src.main.SubtitleOverlay")
    @patch("src.main.pystray")
    @patch("src.main.threading.Thread")
    def test_audio_processing_loop(self, mock_thread, mock_pystray, mock_overlay, mock_trans, mock_whisper, mock_cap, mock_sleep):
        app = PrivaSubApp()
        app.target_language = "Vietnamese"
        app.running = True
        app.is_paused = False
        
        def fake_sleep(secs):
            if app.is_paused:
                app.is_paused = False
                app.running = False
                
        mock_sleep.side_effect = fake_sleep
        
        # Define mock side effects to simulate loop execution and termination
        def fake_get_chunk():
            if not hasattr(app, '_loop_count'):
                app._loop_count = 0
            app._loop_count += 1
            if app._loop_count == 1:
                return [1.0] * 1600 # Valid chunk final
            elif app._loop_count == 2:
                return [1.0] * 1600 # Valid chunk interim
            elif app._loop_count == 3:
                return [1.0] * 1600 # Valid chunk cache reuse
            elif app._loop_count == 4:
                app.is_paused = True # Cover paused condition
                return [1.0] * 1600
            else:
                app.running = False
                return None
                
        app.capture.get_audio_chunk.side_effect = fake_get_chunk
        app.transcriber.process_audio.side_effect = [
            ("hello world", True),
            ("hello interim", False),
            ("hello interim", False),
            ("paused chunk", True)
        ]
        app.translator.translate.return_value = "Xin chào thế giới"
        
        app.audio_processing_loop()
        self.assertFalse(app.running)
        
        # Test window opening methods directly
        app._show_transcriber_win()
        app._show_transcriber_win() # already exists
        app._show_settings_win()
        app._show_settings_win() # already exists
        
        # Test tray icon missing fallback
        with patch("os.path.exists", return_value=False):
            img = app.get_tray_icon_image()
            self.assertIsNotNone(img)

    @patch("src.main.PrivaSubApp")
    @patch("ctypes.windll.kernel32.GetLastError")
    def test_main_function(self, mock_get_last_error, mock_app_class):
        mock_get_last_error.return_value = 0
        mock_app_instance = MagicMock()
        mock_app_class.return_value = mock_app_instance
        
        main()
        mock_app_instance.run.assert_called_once()
        
        # Test main mutex already exists branch
        mock_get_last_error.return_value = 183
        with patch("tkinter.messagebox.showinfo"):
            main()

if __name__ == '__main__':
    unittest.main()
