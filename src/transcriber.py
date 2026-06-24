import os
import sys
import numpy as np
from faster_whisper import WhisperModel

class Transcriber:
    def __init__(self, model_size="tiny.en", device="cpu", compute_type="int8"):
        """
        Initializes the local Whisper transcription engine.
        Using model_size='tiny.en' or 'base.en' and compute_type='int8' for CPU optimization.
        """
        print(f"[AI] Loading Whisper model '{model_size}' on {device} ({compute_type})...")
        # Ensure we run offline first to avoid Hugging Face network requests/timeouts.
        # Fallback to downloading if the model is not found locally.
        try:
            print(f"[AI] Attempting to load Whisper model '{model_size}' from local cache...")
            self.model = WhisperModel(
                model_size, 
                device=device, 
                compute_type=compute_type,
                local_files_only=True
            )
        except Exception as e:
            print(f"[AI] Local model not found or failed to load ({e}). Downloading from Hugging Face...")
            self.model = WhisperModel(
                model_size, 
                device=device, 
                compute_type=compute_type,
                local_files_only=False
            )
        print("[AI] Whisper model loaded successfully.")
        
        # Audio sliding window parameters
        self.sample_rate = 16000
        self.audio_buffer = np.zeros(0, dtype=np.float32)
        
        # Silence detection & text finalization
        self.silence_ticks = 0
        self.speech_detected = False
        self.last_text = ""
        
        # Configuration parameters
        self.max_buffer_seconds = 8.0  # Max length of speech buffer before force-split (optimized for subtitle readability)
        self.silence_threshold_seconds = 1.2  # Silence duration to finalize sentence
        
    def process_audio(self, new_audio_chunk):
        """
        Processes a new chunk of float32 audio.
        Returns:
            (transcript_text, is_final)
            - transcript_text: Current transcribed text string.
            - is_final: True if the user paused speaking (sentence finalized), False otherwise.
        """
        if new_audio_chunk is None or len(new_audio_chunk) == 0:
            return None
            
        # Append new audio to rolling buffer (force float32)
        self.audio_buffer = np.concatenate([self.audio_buffer, new_audio_chunk]).astype(np.float32)
        
        # If the buffer has grown too long (e.g. user speaks without pauses),
        # force split it immediately to avoid latency spikes and memory overload.
        if len(self.audio_buffer) >= (self.max_buffer_seconds * self.sample_rate):
            final_text = self.last_text
            # Keep the last 1 second of audio as context for the next phrase
            context_samples = int(self.sample_rate * 1.0)
            if len(self.audio_buffer) > context_samples:
                self.audio_buffer = self.audio_buffer[-context_samples:]
            else:
                self.audio_buffer = np.zeros(0, dtype=np.float32)
            self.speech_detected = False
            self.last_text = ""
            return final_text, True

        # Perform transcription using faster-whisper's VAD filter
        # We set beam_size=1 for maximum speed/real-time performance
        try:
            segments, info = self.model.transcribe(
                self.audio_buffer,
                beam_size=1,
                vad_filter=True,
                vad_parameters=dict(
                    min_speech_duration_ms=200,
                    max_speech_duration_s=self.max_buffer_seconds,
                    min_silence_duration_ms=400,
                    speech_pad_ms=300
                ),
                language="en"
            )
            segments = list(segments)
        except Exception as e:
            print(f"[AI] Transcription error: {e}")
            return None

        # Process segments
        if not segments:
            # VAD filter determined there's no speech in the current buffer (silence)
            self.silence_ticks += len(new_audio_chunk) / self.sample_rate
            
            # If silence duration exceeds threshold and we had active text, finalize it
            if self.silence_ticks >= self.silence_threshold_seconds and self.speech_detected:
                final_text = self.last_text
                self.reset_buffer()
                return final_text, True
                
            return None
            
        # Speech was successfully transcribed
        self.silence_ticks = 0
        self.speech_detected = True
        
        # Segment-based splitting:
        # If Whisper has identified multiple segments, it means the earlier segments
        # represent completed sentences/clauses. We finalize them immediately and
        # crop the audio buffer to keep only the active segment.
        if len(segments) > 1:
            completed_segments = segments[:-1]
            active_segment = segments[-1]
            
            final_text = " ".join([seg.text for seg in completed_segments]).strip()
            final_text = " ".join(final_text.split())
            
            if final_text:
                active_start_sec = active_segment.start
                buffer_duration = len(self.audio_buffer) / self.sample_rate
                
                if 0 <= active_start_sec < buffer_duration:
                    active_start_sample = int(active_start_sec * self.sample_rate)
                    # Include 0.2s padding context to avoid pop/click audio boundary truncation
                    pad_samples = int(self.sample_rate * 0.2)
                    crop_start = max(0, active_start_sample - pad_samples)
                    self.audio_buffer = self.audio_buffer[crop_start:]
                else:
                    self.audio_buffer = self.audio_buffer[len(self.audio_buffer) // 2:]
                    
                self.last_text = active_segment.text.strip()
                return final_text, True
        
        # Join text from all segments for active/interim transcription
        current_text = " ".join([seg.text for seg in segments]).strip()
        current_text = " ".join(current_text.split())
        self.last_text = current_text
        
        return current_text, False

    def reset_buffer(self):
        """Clears the current audio buffer and resets speech status."""
        self.audio_buffer = np.zeros(0, dtype=np.float32)
        self.silence_ticks = 0
        self.speech_detected = False
        self.last_text = ""
