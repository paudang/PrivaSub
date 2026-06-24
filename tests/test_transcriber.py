import os
import sys
import unittest
import numpy as np

# Add src directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from src.core.ai.transcriber import Transcriber

class TestTranscriber(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load Whisper tiny.en once for testing
        cls.transcriber = Transcriber(model_size="tiny.en", device="cpu", compute_type="int8")

    def setUp(self):
        # Reset the buffer before each test
        self.transcriber.reset_buffer()

    def test_initial_state(self):
        """Verifies that the transcriber initializes with empty buffer and correct sample rate."""
        self.assertEqual(self.transcriber.sample_rate, 16000)
        self.assertEqual(len(self.transcriber.audio_buffer), 0)
        self.assertFalse(self.transcriber.speech_detected)

    def test_silence_vad_filtering(self):
        """Verifies that 1 second of silent audio is correctly filtered by VAD and returns None (no CPU transcription spike)."""
        # Create 1 second of silent float32 samples (16000 samples)
        silent_audio = np.zeros(16000, dtype=np.float32)
        
        result = self.transcriber.process_audio(silent_audio)
        self.assertIsNone(result, "Silent audio should be filtered out by Silero VAD and return None")
        self.assertEqual(len(self.transcriber.audio_buffer), 16000, "Silent audio should still be accumulated in the buffer")

    def test_reset_buffer(self):
        """Checks that reset_buffer correctly clears speech state and audio memory."""
        self.transcriber.audio_buffer = np.ones(16000, dtype=np.float32)
        self.transcriber.speech_detected = True
        self.transcriber.last_text = "Hello"
        
        self.transcriber.reset_buffer()
        
        self.assertEqual(len(self.transcriber.audio_buffer), 0)
        self.assertFalse(self.transcriber.speech_detected)
        self.assertEqual(self.transcriber.last_text, "")

    def test_forced_buffer_split(self):
        """Verifies that when the buffer exceeds max_buffer_seconds, a forced split occurs to prevent latency."""
        # Max buffer is 8.0 seconds (128000 samples)
        # Create a buffer of 9.0 seconds (144000 samples)
        large_audio = np.zeros(144000, dtype=np.float32)
        self.transcriber.speech_detected = True
        self.transcriber.last_text = "Hello world"
        
        result = self.transcriber.process_audio(large_audio)
        
        # When forced split occurs, it returns (last_text, True)
        self.assertIsNotNone(result)
        text, is_final = result
        self.assertEqual(text, "Hello world")
        self.assertTrue(is_final, "Forced split should mark the segment as finalized")
        
        # Audio buffer should be cropped to 1.0 second context (16000 samples)
        self.assertEqual(len(self.transcriber.audio_buffer), 16000)

if __name__ == '__main__':
    unittest.main()
