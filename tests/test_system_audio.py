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

    @patch("src.core.audio.system_audio.time.sleep", return_value=None)
    @patch("src.core.audio.system_audio.pyaudio.PyAudio")
    def test_system_audio_extreme_coverage(self, mock_pyaudio, mock_sleep):
        cap = AudioCapture()
        mock_p = MagicMock()
        mock_pyaudio.return_value = mock_p
        
        # Hit lines 60-65: find_wasapi_loopback_device fallback
        mock_p.get_host_api_info_by_type.return_value = {"defaultOutputDevice": 0}
        mock_p.get_device_info_by_index.return_value = {"name": "Weird Speaker", "isLoopbackDevice": False, "index": 0}
        mock_p.get_loopback_device_info_generator.return_value = [{"name": "Different Loopback", "isLoopbackDevice": True, "index": 1, "defaultSampleRate": 48000, "maxInputChannels": 2}]
        self.assertIsNotNone(cap.find_wasapi_loopback_device())
        
        # Hit lines 84-100: device_switch_requested handling with stream/p exception
        cap.running = True
        cap.device_switch_requested = True
        mock_stream = MagicMock()
        mock_stream.stop_stream.side_effect = Exception("Stop error")
        cap.stream = mock_stream
        mock_p_inst = MagicMock()
        mock_p_inst.terminate.side_effect = Exception("Term error")
        cap.p = mock_p_inst
        
        def fake_sleep1(secs):
            cap.running = False
        mock_sleep.side_effect = fake_sleep1
        cap._record_loop()
        self.assertIsNone(cap.stream)
        self.assertIsNone(cap.p)
        
        # Hit lines 108-139: selected_device_index loopback match
        cap.running = True
        cap.selected_device_index = 1
        mock_stream = MagicMock()
        mock_p.open.return_value = mock_stream
        mock_stream.read.return_value = None # Hit line 212: if not raw_data: continue
        mock_p.get_loopback_device_info_generator.return_value = [{"name": "Matching Loopback", "isLoopbackDevice": True, "index": 1, "defaultSampleRate": 48000, "maxInputChannels": 2}]
        def fake_read1(*args, **kwargs):
            cap.running = False
            return None # empty raw_data
        mock_stream.read.side_effect = fake_read1
        cap._record_loop()
        
        # Hit lines 108-139: selected_device_index standard mic match with 0 channels fallback
        cap.running = True
        cap.p = None
        cap.selected_device_index = 2
        mock_p.get_loopback_device_info_generator.return_value = []
        mock_p.get_device_info_by_index.return_value = {"name": "Standard Mic", "index": 2, "defaultSampleRate": 16000, "maxInputChannels": 0, "maxOutputChannels": 0}
        def fake_read2(*args, **kwargs):
            cap.running = False
            return b"\x00\x00" * 160
        mock_stream.read.side_effect = fake_read2
        cap._record_loop()
        
        # Hit lines 108-139: selected_device_index exception
        cap.running = True
        cap.p = None
        cap.selected_device_index = 999
        mock_p.get_device_info_by_index.side_effect = [Exception("Invalid index"), {"name": "Speaker", "isLoopbackDevice": True, "index": 0, "defaultSampleRate": 48000, "maxInputChannels": 2}]
        mock_p.get_default_input_device_info.return_value = {"name": "Default Mic", "index": 0, "defaultSampleRate": 16000, "maxInputChannels": 0} # Hit lines 155-161: default device channels 0 fallback
        def fake_read3(*args, **kwargs):
            cap.running = False
            return b"\x00\x00" * 160
        mock_stream.read.side_effect = fake_read3
        cap._record_loop()
        
        # Hit line 198: fallback open success (open fails first time, succeeds second time)
        cap.running = True
        cap.p = None
        cap.selected_device_index = None
        mock_p.get_device_info_by_index.side_effect = None
        mock_p.get_device_info_by_index.return_value = {"name": "Speaker", "isLoopbackDevice": True, "index": 0, "defaultSampleRate": 48000, "maxInputChannels": 2}
        mock_stream_fallback = MagicMock()
        mock_p.open.side_effect = [Exception("First open fail"), mock_stream_fallback]
        def fake_read4(*args, **kwargs):
            cap.running = False
            return b"\x00\x00" * 160
        mock_stream_fallback.read.side_effect = fake_read4
        cap._record_loop()
        
        # Hit lines 238-239, 242-243: read exception with stream stop/pyaudio terminate exception
        cap.running = True
        cap.p = None
        mock_p.open.side_effect = None
        mock_p.open.return_value = mock_stream
        def fake_read5(*args, **kwargs):
            cap.running = False
            mock_stream.stop_stream.side_effect = Exception("Error stopping")
            mock_p.terminate.side_effect = Exception("Error terminating")
            raise Exception("Force read error")
        mock_stream.read.side_effect = fake_read5
        cap._record_loop()
        
        mock_stream.stop_stream.side_effect = None
        mock_p.terminate.side_effect = None
        
        # Hit line 293: get_audio_chunk empty return None
        cap2 = AudioCapture()
        self.assertIsNone(cap2.get_audio_chunk())
        
        # Hit lines 325-326: get_available_devices exception
        mock_p.get_loopback_device_info_generator.side_effect = Exception("Generator error")
        cap2.get_available_devices()
        
        # Hit lines 253-254, 258-259: cleanup on exit exceptions
        cap3 = AudioCapture()
        cap3.running = True
        cap3.p = mock_p
        cap3.stream = mock_stream
        mock_p.open.return_value = mock_stream
        mock_p.open.side_effect = None
        def fake_read_cap3(*args, **kwargs):
            cap3.running = False
            return b"\x00\x00" * 160
        mock_stream.read.side_effect = fake_read_cap3
        mock_stream.stop_stream.side_effect = Exception("Exit stop error")
        mock_p.terminate.side_effect = Exception("Exit term error")
        cap3._record_loop()

if __name__ == '__main__':
    unittest.main()
