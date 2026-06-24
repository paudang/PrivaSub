import unittest
from unittest.mock import patch, MagicMock

# Mock ctypes before importing ui to avoid Windows-specific errors on other OS
import sys
import builtins

# Create a mock for ctypes if testing on non-Windows
if sys.platform != "win32":
    import ctypes
    ctypes.windll = MagicMock()

import customtkinter as ctk
from src.ui.live.overlay import SubtitleOverlay
from src.core.config import DEFAULT_CONFIG

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

if __name__ == "__main__":
    unittest.main()
