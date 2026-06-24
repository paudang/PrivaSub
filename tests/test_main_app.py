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
        
        # Test exit
        app.on_exit(None, None)
        self.assertFalse(app.running)

    @patch("src.main.PrivaSubApp")
    @patch("ctypes.windll.kernel32.GetLastError")
    def test_main_function(self, mock_get_last_error, mock_app_class):
        mock_get_last_error.return_value = 0
        mock_app_instance = MagicMock()
        mock_app_class.return_value = mock_app_instance
        
        main()
        mock_app_instance.run.assert_called_once()

if __name__ == '__main__':
    unittest.main()
