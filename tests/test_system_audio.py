import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from src.core.audio.system_audio import AudioCapture, HAS_WPATCH

class TestSystemAudio(unittest.TestCase):
    def test_init_and_resample(self):
        cap = AudioCapture(sample_rate=16000, chunk_duration_ms=100)
        self.assertEqual(cap.target_rate, 16000)
        
        # Test resample same rate
        data = np.zeros(1600, dtype=np.float32)
        res = cap.resample(data, 16000, 16000)
        self.assertTrue(np.array_equal(data, res))
        
        # Test resample different rate
        data_48k = np.zeros(4800, dtype=np.float32)
        res_16k = cap.resample(data_48k, 48000, 16000)
        self.assertEqual(len(res_16k), 1600)
        
    @patch("src.core.audio.system_audio.HAS_WPATCH", True)
    @patch("src.core.audio.system_audio.pyaudio.PyAudio")
    def test_find_wasapi_loopback_device(self, mock_pyaudio):
        cap = AudioCapture()
        mock_p = MagicMock()
        mock_pyaudio.return_value = mock_p
        
        # Case 1: default speaker is loopback
        mock_p.get_host_api_info_by_type.return_value = {"defaultOutputDevice": 0}
        mock_p.get_device_info_by_index.return_value = {"name": "Speaker", "isLoopbackDevice": True, "index": 0, "defaultSampleRate": 48000, "maxInputChannels": 2}
        dev = cap.find_wasapi_loopback_device()
        self.assertIsNotNone(dev)
        
        # Case 2: default speaker not loopback, matching loopback found
        mock_p.get_device_info_by_index.return_value = {"name": "Speaker", "isLoopbackDevice": False, "index": 0}
        mock_p.get_loopback_device_info_generator.return_value = [{"name": "Speaker (Loopback)", "isLoopbackDevice": True, "index": 1, "defaultSampleRate": 48000, "maxInputChannels": 2}]
        dev2 = cap.find_wasapi_loopback_device()
        self.assertIsNotNone(dev2)
        
        # Case 3: IOError in get_host_api_info_by_type
        mock_p.get_host_api_info_by_type.side_effect = IOError("No WASAPI")
        dev3 = cap.find_wasapi_loopback_device()
        self.assertIsNone(dev3)

    @patch("src.core.audio.system_audio.HAS_WPATCH", False)
    def test_find_wasapi_no_wpatch(self):
        cap = AudioCapture()
        self.assertIsNone(cap.find_wasapi_loopback_device())

    @patch("src.core.audio.system_audio.time.sleep", return_value=None)
    @patch("src.core.audio.system_audio.pyaudio.PyAudio")
    def test_record_loop_and_controls(self, mock_pyaudio, mock_sleep):
        cap = AudioCapture()
        mock_p = MagicMock()
        mock_pyaudio.return_value = mock_p
        
        def fake_sleep(secs):
            if cap.paused:
                cap.paused = False
                cap.running = False
        mock_sleep.side_effect = fake_sleep
        
        # Mock device info to return proper integers for rate and channels
        mock_p.get_host_api_info_by_type.return_value = {"defaultOutputDevice": 0}
        mock_p.get_device_info_by_index.return_value = {
            "name": "Speaker",
            "isLoopbackDevice": True,
            "index": 0,
            "defaultSampleRate": 16000,
            "maxInputChannels": 1
        }
        mock_p.get_default_input_device_info.return_value = {"name": "Mic", "index": 0, "defaultSampleRate": 16000, "maxInputChannels": 1}
        
        mock_stream = MagicMock()
        mock_p.open.return_value = mock_stream
        
        # Simulate stream.read returning valid audio bytes once, then set running to False
        raw_bytes = np.zeros(1600, dtype=np.int16).tobytes()
        
        def fake_read(*args, **kwargs):
            if not hasattr(cap, '_read_count'):
                cap._read_count = 0
            cap._read_count += 1
            if cap._read_count == 1:
                return raw_bytes
            elif cap._read_count == 2:
                # Cover pause
                cap.paused = True
                return raw_bytes
            else:
                cap.running = False
                return None
                
        mock_stream.read.side_effect = fake_read
        
        cap.running = True
        cap._record_loop()
        
        # Verify queue has chunk
        chunk = cap.get_audio_chunk()
        self.assertIsNotNone(chunk)
        
        # Test controls
        with patch("threading.Thread.start"), patch("threading.Thread.join"):
            cap.start()
            cap.start() # already running
            cap.pause()
            self.assertTrue(cap.paused)
            cap.resume()
            self.assertFalse(cap.paused)
            cap.stop()
            self.assertFalse(cap.running)
            
    @patch("src.core.audio.system_audio.time.sleep", return_value=None)
    @patch("src.core.audio.system_audio.pyaudio.PyAudio")
    def test_record_loop_stereo_and_exceptions(self, mock_pyaudio, mock_sleep):
        cap = AudioCapture()
        mock_p = MagicMock()
        mock_pyaudio.return_value = mock_p
        
        def fake_sleep(secs):
            cap.running = False
        mock_sleep.side_effect = fake_sleep
        
        # Mock stereo input device info
        mock_p.get_host_api_info_by_type.return_value = {"defaultOutputDevice": 0}
        mock_p.get_device_info_by_index.return_value = {
            "name": "Stereo Speaker",
            "isLoopbackDevice": True,
            "index": 0,
            "defaultSampleRate": 48000,
            "maxInputChannels": 2
        }
        mock_p.get_default_input_device_info.return_value = {"name": "Stereo Mic", "index": 0, "defaultSampleRate": 48000, "maxInputChannels": 2}
        mock_stream = MagicMock()
        mock_p.open.return_value = mock_stream
        
        # Stereo bytes
        raw_bytes = np.zeros((4800, 2), dtype=np.int16).tobytes()
        
        def fake_read(*args, **kwargs):
            if not hasattr(cap, '_read_count2'):
                cap._read_count2 = 0
            cap._read_count2 += 1
            if cap._read_count2 == 1:
                return raw_bytes
            elif cap._read_count2 == 2:
                cap.running = False
                raise Exception("Stream read error")
            return None
            
        mock_stream.read.side_effect = fake_read
        
        cap.running = True
        cap._record_loop()
        self.assertFalse(cap.running)
        
        # Test open stream exception
        mock_p.open.side_effect = Exception("Open error")
        cap.running = True
        cap._record_loop()
        self.assertFalse(cap.running)
        
        # Test no input device found
        mock_p.get_host_api_info_by_type.side_effect = IOError("No WASAPI")
        mock_p.get_default_input_device_info.side_effect = IOError("No device")
        cap.running = True
        cap._record_loop()
        self.assertFalse(cap.running)

    @patch("src.core.audio.system_audio.pyaudio.PyAudio")
    def test_device_selection(self, mock_pyaudio):
        cap = AudioCapture()
        mock_p = MagicMock()
        mock_pyaudio.return_value = mock_p
        
        mock_p.get_loopback_device_info_generator.return_value = [{"index": 1, "name": "Speaker Loopback", "maxInputChannels": 2, "defaultSampleRate": 48000}]
        mock_p.get_device_count.return_value = 1
        mock_p.get_device_info_by_index.return_value = {"index": 0, "name": "Mic", "maxInputChannels": 1, "defaultSampleRate": 16000, "isLoopbackDevice": False}
        
        devices = cap.get_available_devices()
        self.assertGreaterEqual(len(devices), 1)
        
        cap.set_device(1)
        self.assertEqual(cap.selected_device_index, 1)
        
        # Test record loop with selected device
        mock_stream = MagicMock()
        mock_p.open.return_value = mock_stream
        mock_stream.read.return_value = None
        
        # Will exit loop immediately because read returns None and running becomes False
        cap.running = False
        cap._record_loop()

if __name__ == '__main__':
    unittest.main()
