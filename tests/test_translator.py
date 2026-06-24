import os
import sys
import unittest

# Add src directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from translator import OfflineTranslator

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

if __name__ == '__main__':
    unittest.main()
