import os
import sys
import unittest
import wave
import struct
import math

# Add src directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from src.core.audio.file_extractor import extract_audio_to_wav

class TestAudioExtractor(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.dirname(__file__)
        self.input_wav = os.path.join(self.test_dir, "temp_input.wav")
        self.output_wav = os.path.join(self.test_dir, "temp_output.wav")
        
        # Create a dummy 1-second 44100Hz stereo WAV file to test extraction/resampling
        sample_rate = 44100
        duration = 1.0
        num_samples = int(sample_rate * duration)
        
        with wave.open(self.input_wav, 'w') as wav:
            wav.setnchannels(2)  # Stereo
            wav.setsampwidth(2)   # 16-bit
            wav.setframerate(sample_rate)
            
            # Simple 440Hz sine wave
            for i in range(num_samples):
                val = int(32767.0 * 0.5 * math.sin(2.0 * math.pi * 440.0 * i / sample_rate))
                data = struct.pack('<hh', val, val)  # Left & Right
                wav.writeframesraw(data)

    def tearDown(self):
        # Clean up temporary test files
        for f in [self.input_wav, self.output_wav]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

    def test_audio_extraction_and_resampling(self):
        """Verifies that PyAV extracts stereo 44.1kHz audio and outputs a correct 16kHz mono WAV file."""
        # Run extraction
        success = extract_audio_to_wav(self.input_wav, self.output_wav)
        self.assertTrue(success, "Audio extraction failed")
        self.assertTrue(os.path.exists(self.output_wav), "Output WAV file was not created")
        
        # Verify output WAV properties
        with wave.open(self.output_wav, 'r') as wav:
            channels = wav.getnchannels()
            sample_width = wav.getsampwidth()
            framerate = wav.getframerate()
            num_frames = wav.getnframes()
            
            self.assertEqual(channels, 1, "Output WAV should be mono (1 channel)")
            self.assertEqual(sample_width, 2, "Output WAV sample width should be 2 bytes (s16 PCM)")
            self.assertEqual(framerate, 16000, "Output WAV framerate should be resampled to 16000Hz")
            
            # 1 second of 16kHz audio should have ~16000 frames
            self.assertAlmostEqual(num_frames, 16000, delta=100)

if __name__ == '__main__':
    unittest.main()
