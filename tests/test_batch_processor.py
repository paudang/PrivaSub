import os
import sys
import unittest
import wave
import struct
import math

# Add src directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from src.services.batch_processor import BatchTranscriber, format_timestamp

class TestBatchProcessor(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.dirname(__file__)
        self.test_audio = os.path.join(self.test_dir, "temp_test_audio.wav")
        self.output_srt = os.path.join(self.test_dir, "temp_test_audio.srt")
        self.output_vtt = os.path.join(self.test_dir, "temp_test_audio.vtt")
        
        # Generate a simple 16kHz mono 2-second WAV file
        sample_rate = 16000
        duration = 2.0
        num_samples = int(sample_rate * duration)
        
        with wave.open(self.test_audio, 'w') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            
            for i in range(num_samples):
                val = int(32767.0 * 0.5 * math.sin(2.0 * math.pi * 440.0 * i / sample_rate))
                data = struct.pack('<h', val)
                wav.writeframesraw(data)

    def tearDown(self):
        # Clean up files
        for f in [self.test_audio, self.output_srt, self.output_vtt]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

    def test_timestamp_formatting(self):
        """Verifies standard timestamp conversions for both SRT and VTT formats."""
        # SRT Format (commas for decimal separator)
        self.assertEqual(format_timestamp(0.0, is_vtt=False), "00:00:00,000")
        self.assertEqual(format_timestamp(3661.123, is_vtt=False), "01:01:01,123")
        
        # VTT Format (dots for decimal separator)
        self.assertEqual(format_timestamp(0.0, is_vtt=True), "00:00:00.000")
        self.assertEqual(format_timestamp(3661.123, is_vtt=True), "01:01:01.123")

    def test_batch_transcription_srt(self):
        """Tests transcribing to English SRT format."""
        transcriber = BatchTranscriber(model_size="tiny.en", device="cpu", compute_type="int8")
        
        result_path = transcriber.process_file(
            input_path=self.test_audio,
            output_mode="en",
            output_format="srt"
        )
        
        self.assertEqual(result_path, self.output_srt)
        self.assertTrue(os.path.exists(self.output_srt), "SRT output file should be created")
        
        # Verify file content
        with open(self.output_srt, "r", encoding="utf-8") as f:
            content = f.read()
        
        # SRT should not have WEBVTT header
        self.assertFalse(content.startswith("WEBVTT"))

    def test_batch_transcription_vtt_vi(self):
        """Tests transcribing to Vietnamese VTT format."""
        transcriber = BatchTranscriber(model_size="tiny.en", device="cpu", compute_type="int8")
        
        result_path = transcriber.process_file(
            input_path=self.test_audio,
            output_mode="vi",
            output_format="vtt"
        )
        
        self.assertEqual(result_path, self.output_vtt)
        self.assertTrue(os.path.exists(self.output_vtt), "VTT output file should be created")
        
        # Verify file content
        with open(self.output_vtt, "r", encoding="utf-8") as f:
            content = f.read()
            
        # VTT should start with WEBVTT
        self.assertTrue(content.startswith("WEBVTT"))

if __name__ == '__main__':
    unittest.main()
