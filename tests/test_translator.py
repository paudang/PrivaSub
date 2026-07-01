import os
import sys
import unittest
from unittest.mock import patch

# Add src directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from src.core.ai.translator import OfflineTranslator

class TestTranslator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize translator once for all tests to speed up execution
        cls.translator = OfflineTranslator()

    def test_basic_translation(self):
        """Verifies simple sentence translation output."""
        en_text = "Welcome to PrivaSub"
        vi_text = self.translator.translate(en_text)
        
        self.assertIsNotNone(vi_text)
        self.assertTrue(len(vi_text) > 0)
        # Check translation contains some Vietnamese words (like "Chào mừng" or "đến")
        self.assertTrue(any(word in vi_text.lower() for word in ["chào", "đến", "mừng", "privasub"]), 
                        f"Unexpected translation: {vi_text}")

    def test_capitalization_preprocessing(self):
        """Checks that sentences starting with lowercase letters are capitalized and translated correctly."""
        en_text = "hello how are you"
        vi_text = self.translator.translate(en_text)
        
        # Output should be natural and not have a trailing period unless explicitly wanted,
        # but it should have correct semantic translation.
        self.assertTrue(any(word in vi_text.lower() for word in ["chào", "khỏe", "bạn"]), 
                        f"Unexpected translation: {vi_text}")

    def test_punctuation_handling(self):
        """Checks that sentences without ending punctuation receive proper context periods and are post-processed correctly."""
        # 1. Without period
        en_text_no_punc = "I want to go to the store"
        vi_text_no_punc = self.translator.translate(en_text_no_punc)
        
        # 2. With period
        en_text_with_punc = "I want to go to the store."
        vi_text_with_punc = self.translator.translate(en_text_with_punc)
        
        # The translations should be semantically equivalent
        self.assertFalse(vi_text_no_punc.endswith('.'), "Trailing period was not stripped in post-processing")
        self.assertTrue(any(word in vi_text_no_punc.lower() for word in ["muốn", "đi", "hàng"]), 
                        f"Unexpected translation: {vi_text_no_punc}")

    def test_empty_string_handling(self):
        """Verifies that empty or whitespace strings return an empty string safely."""
        self.assertEqual(self.translator.translate(""), "")
        self.assertEqual(self.translator.translate("   "), "")
        self.assertEqual(self.translator.translate(None), "")

    def test_translation_error_handling(self):
        with patch.object(self.translator.tokenizer, 'convert_ids_to_tokens', side_effect=Exception("Test Error")):
            result = self.translator.translate("Hello")
            # In case of error, it should log and return the original text
            self.assertEqual(result, "Hello")
            
    def test_set_translation_direction(self):
        self.translator.set_translation_direction("vi", "en")
        self.assertEqual(self.translator.source_lang, "vi")
        self.assertEqual(self.translator.target_lang, "en")
        if self.translator.tokenizer:
            self.assertEqual(self.translator.tokenizer.src_lang, "vie_Latn")
        
        # Test no-op if same direction
        self.translator.set_translation_direction("vi", "en")
        
        # Restore back to original working state for other tests
        self.translator.set_translation_direction("en", "vi")
        if self.translator.tokenizer:
            self.assertEqual(self.translator.tokenizer.src_lang, "eng_Latn")
            
    def test_model_download_logic(self):
        with patch('src.core.ai.translator.os.path.exists') as mock_exists:
            # First 5 calls check if model files exist, return False to trigger download
            mock_exists.return_value = False
            
            with patch('src.core.ai.translator.snapshot_download') as mock_download:
                with patch('src.core.ai.translator.os.makedirs'):
                    # Create translator with dummy path
                    with patch.object(OfflineTranslator, '_load_model'):
                        translator = OfflineTranslator(model_dir="dummy/path")
                        mock_download.assert_called_once()

    def test_translate_uninitialized(self):
        """Checks translation fallback when translator or tokenizer is None."""
        orig_translator = self.translator.translator
        self.translator.translator = None
        try:
            result = self.translator.translate("Hello")
            self.assertEqual(result, "Hello")
        finally:
            self.translator.translator = orig_translator

    def test_download_error(self):
        """Verifies that snapshot_download failure raises RuntimeError."""
        with patch('src.core.ai.translator.os.path.exists', return_value=False):
            with patch('src.core.ai.translator.snapshot_download', side_effect=Exception("API Error")):
                with patch('src.core.ai.translator.os.makedirs'):
                    with self.assertRaises(RuntimeError):
                        OfflineTranslator(model_dir="dummy/path")

if __name__ == '__main__':
    unittest.main()
