import queue
import threading
import time
import numpy as np

# We try to import pyaudiowpatch (for Windows loopback), 
# and fall back to standard pyaudio on other platforms.
try:
    import pyaudiowpatch as pyaudio
    HAS_WPATCH = True
except ImportError:
    import pyaudio
    HAS_WPATCH = False

class AudioCapture:
    def __init__(self, sample_rate=16000, chunk_duration_ms=100):
        self.target_rate = sample_rate
        self.chunk_duration_ms = chunk_duration_ms
        self.audio_queue = queue.Queue()
        self.running = False
        self.paused = False
        self.thread = None
        self.p = None
        self.stream = None
        
        # Audio device info
        self.device_index = None
        self.device_name = "Default"
        self.device_rate = 16000
        self.device_channels = 1
        
    def find_wasapi_loopback_device(self):
        """Finds the default WASAPI loopback device for Windows."""
        if not HAS_WPATCH:
            return None
            
        p = pyaudio.PyAudio()
        try:
            wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
        except IOError:
            p.terminate()
            return None
            
        default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
        
        # Check if default speakers are already a loopback device
        if default_speakers.get("isLoopbackDevice", False):
            p.terminate()
            return default_speakers
            
        # Otherwise, search loopback devices matching the default speaker's name
        for loopback in p.get_loopback_device_info_generator():
            if default_speakers["name"] in loopback["name"]:
                p.terminate()
                return loopback
                
        # Fallback to any loopback device
        for loopback in p.get_loopback_device_info_generator():
            p.terminate()
            return loopback
            
        p.terminate()
        return None

    def resample(self, audio_data, orig_sr, target_sr=16000):
        """Linearly resamples audio from orig_sr to target_sr using numpy."""
        if orig_sr == target_sr:
            return audio_data
        duration = len(audio_data) / orig_sr
        num_samples = int(duration * target_sr)
        x_orig = np.linspace(0, duration, len(audio_data))
        x_target = np.linspace(0, duration, num_samples)
        return np.interp(x_target, x_orig, audio_data).astype(np.float32)

    def _record_loop(self):
        self.p = pyaudio.PyAudio()
        
        # Determine device settings
        loopback_device = self.find_wasapi_loopback_device()
        
        if loopback_device:
            self.device_index = loopback_device["index"]
            self.device_name = loopback_device["name"]
            self.device_rate = int(loopback_device["defaultSampleRate"])
            self.device_channels = loopback_device["maxInputChannels"]
            print(f"[Audio] Using WASAPI Loopback device: {self.device_name} (Rate: {self.device_rate}, Channels: {self.device_channels})")
        else:
            # Fallback to default input (e.g. microphone or virtual audio cable)
            try:
                default_device = self.p.get_default_input_device_info()
                self.device_index = default_device["index"]
                self.device_name = default_device["name"]
                self.device_rate = int(default_device["defaultSampleRate"])
                self.device_channels = default_device["maxInputChannels"]
                print(f"[Audio] Fallback to default input device: {self.device_name} (Rate: {self.device_rate}, Channels: {self.device_channels})")
            except IOError:
                print("[Audio] Error: No input or loopback audio devices found.")
                self.running = False
                self.p.terminate()
                return

        # Calculate chunk size (frames per buffer) based on native device sample rate
        chunk_size = int(self.device_rate * (self.chunk_duration_ms / 1000.0))
        
        try:
            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=self.device_channels,
                rate=self.device_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=chunk_size
            )
        except Exception as e:
            print(f"[Audio] Error opening stream: {e}")
            self.running = False
            self.p.terminate()
            return
            
        print("[Audio] Recording started.")
        
        while self.running:
            if self.paused:
                time.sleep(0.1)
                continue
                
            try:
                # Read raw bytes from the stream
                raw_data = self.stream.read(chunk_size, exception_on_overflow=False)
                if not raw_data:
                    continue
                    
                # Convert bytes to numpy 16-bit integer array
                audio_np = np.frombuffer(raw_data, dtype=np.int16)
                
                # Reshape to channels if stereo/multi-channel
                if self.device_channels > 1:
                    audio_np = audio_np.reshape(-1, self.device_channels)
                    # Downmix to mono by averaging channels
                    audio_np = audio_np.mean(axis=1)
                
                # Convert to float32 and normalize to [-1.0, 1.0]
                audio_float32 = audio_np.astype(np.float32) / 32768.0
                
                # Resample to 16kHz
                audio_resampled = self.resample(audio_float32, self.device_rate, self.target_rate)
                
                # Put the processed chunk into queue
                self.audio_queue.put(audio_resampled)
                
            except Exception as e:
                print(f"[Audio] Stream read error: {e}")
                time.sleep(0.1)
                
        # Clean up
        try:
            self.stream.stop_stream()
            self.stream.close()
        except:
            pass
        self.p.terminate()
        print("[Audio] Recording stopped and cleaned up.")

    def start(self):
        if self.running:
            return
        self.running = True
        self.paused = False
        self.thread = threading.Thread(target=self._record_loop, daemon=True)
        self.thread.start()
        
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
            
    def pause(self):
        self.paused = True
        print("[Audio] Capturing paused.")
        
    def resume(self):
        self.paused = False
        print("[Audio] Capturing resumed.")
        
    def get_audio_chunk(self):
        """Helper to get processed audio chunks from the queue (non-blocking)."""
        chunks = []
        try:
            while True:
                chunks.append(self.audio_queue.get_nowait())
        except queue.Empty:
            pass
        if chunks:
            return np.concatenate(chunks).astype(np.float32)
        return None
