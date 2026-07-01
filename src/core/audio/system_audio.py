import queue
import threading
import time
import numpy as np

from src.core.audio.device_manager import (
    pyaudio,
    HAS_WPATCH,
    find_wasapi_loopback_device,
    get_available_devices
)

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
        self.selected_device_index = None
        self.device_switch_requested = False

    def find_wasapi_loopback_device(self):
        """Proxy to find_wasapi_loopback_device in device_manager."""
        return find_wasapi_loopback_device()

    def resample(self, audio_data, orig_sr, target_sr=16000):
        """Resamples audio from orig_sr to target_sr using fast decimation or cached linear interpolation."""
        if orig_sr == target_sr:
            return audio_data
            
        # Fast path: if native device rate is a direct multiple of 16000 (e.g. 48000Hz or 32000Hz),
        # perform zero-allocation decimation (slicing) which runs in O(1) time.
        if orig_sr % target_sr == 0:
            step = orig_sr // target_sr
            return audio_data[::step]
            
        # Slow path fallback: cached linear interpolation (avoids repeating np.linspace on every chunk)
        cache_key = (len(audio_data), orig_sr)
        if not hasattr(self, '_resample_cache'):
            self._resample_cache = {}
            
        if cache_key not in self._resample_cache:
            duration = len(audio_data) / orig_sr
            num_samples = int(duration * target_sr)
            x_orig = np.linspace(0, duration, len(audio_data), dtype=np.float32)
            x_target = np.linspace(0, duration, num_samples, dtype=np.float32)
            self._resample_cache[cache_key] = (x_target, x_orig)
            
        x_target, x_orig = self._resample_cache[cache_key]
        return np.interp(x_target, x_orig, audio_data).astype(np.float32)

    def _record_loop(self):
        while self.running:
            if self.paused:
                time.sleep(0.1)
                continue
                
            if getattr(self, 'device_switch_requested', False):
                print("[Audio] Processing requested device switch on audio thread...")
                self.device_switch_requested = False
                if self.stream:
                    try:
                        self.stream.stop_stream()
                        self.stream.close()
                    except:
                        pass
                if self.p:
                    try:
                        self.p.terminate()
                    except:
                        pass
                self.p = None
                self.stream = None
                time.sleep(0.2)
                continue
                
            if self.p is None:
                self.p = pyaudio.PyAudio()
                
                # Determine device settings
                is_loopback_mode = False
                if self.selected_device_index is not None:
                    try:
                        # First check if the selected device index matches any loopback device
                        loopback_match = None
                        if HAS_WPATCH:
                            for loopback in self.p.get_loopback_device_info_generator():
                                if loopback["index"] == self.selected_device_index:
                                    loopback_match = loopback
                                    break
                        
                        if loopback_match:
                            self.device_index = loopback_match["index"]
                            self.device_name = loopback_match["name"]
                            self.device_rate = int(loopback_match["defaultSampleRate"])
                            self.device_channels = loopback_match["maxInputChannels"]
                            is_loopback_mode = True
                            print(f"[Audio] Using selected WASAPI Loopback device: {self.device_name} (Rate: {self.device_rate}, Channels: {self.device_channels})")
                        else:
                            # Standard input device (e.g. microphone)
                            dev_info = self.p.get_device_info_by_index(self.selected_device_index)
                            self.device_index = dev_info["index"]
                            self.device_name = dev_info["name"]
                            self.device_rate = int(dev_info["defaultSampleRate"])
                            self.device_channels = dev_info["maxInputChannels"]
                            if self.device_channels == 0:
                                # Fallback to 1 channel or 2 channels if maxInputChannels is 0 but user forced it
                                self.device_channels = dev_info.get("maxOutputChannels", 2)
                                if self.device_channels == 0:
                                    self.device_channels = 1
                            print(f"[Audio] Using selected input device: {self.device_name} (Rate: {self.device_rate}, Channels: {self.device_channels})")
                    except Exception as e:
                        print(f"[Audio] Failed to use selected device {self.selected_device_index}: {e}")
                        self.selected_device_index = None
                
                if self.selected_device_index is None:
                    loopback_device = find_wasapi_loopback_device()
                    
                    if loopback_device:
                        self.device_index = loopback_device["index"]
                        self.device_name = loopback_device["name"]
                        self.device_rate = int(loopback_device["defaultSampleRate"])
                        self.device_channels = loopback_device["maxInputChannels"]
                        is_loopback_mode = True
                        print(f"[Audio] Using default WASAPI Loopback device: {self.device_name} (Rate: {self.device_rate}, Channels: {self.device_channels})")
                    else:
                        # Fallback to default input (e.g. microphone or virtual audio cable)
                        try:
                            default_device = self.p.get_default_input_device_info()
                            self.device_index = default_device["index"]
                            self.device_name = default_device["name"]
                            self.device_rate = int(default_device["defaultSampleRate"])
                            self.device_channels = default_device["maxInputChannels"]
                            if self.device_channels == 0:
                                self.device_channels = 1
                            print(f"[Audio] Fallback to default input device: {self.device_name} (Rate: {self.device_rate}, Channels: {self.device_channels})")
                        except IOError:
                            print("[Audio] Error: No input or loopback audio devices found.")
                            self.running = False
                            self.p.terminate()
                            self.p = None
                            return

                # Calculate chunk size (frames per buffer) based on native device sample rate
                chunk_size = int(self.device_rate * (self.chunk_duration_ms / 1000.0))
                
                try:
                    open_kwargs = {
                        "format": pyaudio.paInt16,
                        "channels": self.device_channels,
                        "rate": self.device_rate,
                        "input": True,
                        "input_device_index": self.device_index,
                        "frames_per_buffer": chunk_size
                    }
                    self.stream = self.p.open(**open_kwargs)
                    print("[Audio] Recording started successfully.")
                except Exception as e:
                    print(f"[Audio] Error opening stream (trying fallback parameters): {e}")
                    # Try fallback without as_loopback or with 1 channel if it failed
                    try:
                        self.stream = self.p.open(
                            format=pyaudio.paInt16,
                            channels=1,
                            rate=self.device_rate,
                            input=True,
                            input_device_index=self.device_index,
                            frames_per_buffer=chunk_size
                        )
                        print("[Audio] Recording started with fallback 1-channel settings.")
                    except Exception as e2:
                        print(f"[Audio] Fatal error opening stream: {e2}")
                        self.p.terminate()
                        self.p = None
                        time.sleep(1.0)
                        continue
            
            try:
                # Calculate chunk size dynamically in case it wasn't set in this scope
                chunk_size = int(self.device_rate * (self.chunk_duration_ms / 1000.0))
                # Read raw bytes from the stream
                raw_data = self.stream.read(chunk_size, exception_on_overflow=False)
                if not raw_data:
                    continue
                    
                # Convert bytes to numpy 16-bit integer array
                audio_np = np.frombuffer(raw_data, dtype=np.int16)
                
                # Reshape and downmix to mono (with optimized stereo fast path)
                if self.device_channels == 2:
                    n_frames = len(audio_np) // 2
                    audio_float32 = (audio_np[0:2*n_frames:2].astype(np.float32) + audio_np[1:2*n_frames:2].astype(np.float32)) / 65536.0
                elif self.device_channels > 2:
                    audio_np = audio_np.reshape(-1, self.device_channels)
                    # Downmix to mono by averaging channels
                    audio_np = audio_np.mean(axis=1)
                    audio_float32 = audio_np.astype(np.float32) / 32768.0
                else:
                    audio_float32 = audio_np.astype(np.float32) / 32768.0
                
                # Resample to 16kHz
                audio_resampled = self.resample(audio_float32, self.device_rate, self.target_rate)
                
                # Put the processed chunk into queue
                self.audio_queue.put(audio_resampled)
                
            except Exception as e:
                print(f"[Audio] Stream read error (device reset/reconnected): {e}")
                # Close broken stream and reset PyAudio to trigger auto-reinitialization on next loop
                try:
                    self.stream.stop_stream()
                    self.stream.close()
                except:
                    pass
                try:
                    self.p.terminate()
                except:
                    pass
                self.p = None
                self.stream = None
                time.sleep(0.5)
                
        # Clean up on exit
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
        if self.p:
            try:
                self.p.terminate()
            except:
                pass
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

    def get_available_devices(self):
        """Returns a list of dicts with available WASAPI loopback and unique input devices."""
        return get_available_devices()

    def set_device(self, device_index):
        """Switches the active recording device safely without C-level memory conflicts."""
        print(f"[Audio] Requesting device switch to index {device_index}")
        self.selected_device_index = device_index
        self.device_switch_requested = True
