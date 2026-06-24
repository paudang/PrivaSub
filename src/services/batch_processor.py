import os
import sys
import time
import logging
from faster_whisper import WhisperModel
from src.core.ai.translator import OfflineTranslator
from src.core.audio.file_extractor import extract_audio_to_wav

logger = logging.getLogger("PrivaSub.BatchProcessor")

def format_timestamp(seconds: float, is_vtt: bool = False) -> str:
    """Formats float seconds into HH:MM:SS,mmm (SRT) or HH:MM:SS.mmm (VTT) format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int(round((seconds - int(seconds)) * 1000))
    # Correct rounding overflow (e.g. 1000ms -> +1s)
    if milliseconds >= 1000:
        milliseconds -= 1000
        secs += 1
        if secs >= 60:
            secs -= 60
            minutes += 1
            if minutes >= 60:
                minutes -= 60
                hours += 1
                
    separator = "." if is_vtt else ","
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{separator}{milliseconds:03d}"

class BatchTranscriber:
    """
    Coordinates offline video/audio file transcription, translation, and subtitle export (SRT/VTT).
    """
    def __init__(self, model_size="tiny.en", device="cpu", compute_type="int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.translator = None

    def _get_translator(self):
        """Lazy loads the translator model to conserve RAM when not needed."""
        if not self.translator:
            logger.info("Initializing OfflineTranslator for batch translation...")
            self.translator = OfflineTranslator(device=self.device, compute_type=self.compute_type)
        return self.translator

    def process_file(self, input_path: str, output_mode="dual", output_format="srt", progress_callback=None) -> str:
        """
        Extracts audio, transcribes, translates (if needed), and saves standard subtitles next to the file.
        
        :param input_path: Path to the input video or audio file.
        :param output_mode: "en" (English only), "vi" (Vietnamese only), or "dual" (both).
        :param output_format: "srt" or "vtt".
        :param progress_callback: Optional function(progress_percent: float, status_text: str) to report progress.
        :return: Path to the generated subtitles file, or None on error.
        """
        temp_wav_path = None
        try:
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Input file not found: {input_path}")

            # Define output path next to the video file
            base_path, _ = os.path.splitext(input_path)
            output_ext = f".{output_format}"
            output_path = base_path + output_ext

            # Create temp wav path inside the same folder (or system temp)
            temp_wav_path = base_path + "_temp_audio.wav"

            # Step 1: Audio Extraction (takes 0% to 30% of progress)
            if progress_callback:
                progress_callback(0.0, "Extracting audio from video file...")

            def extraction_callback(percent):
                if progress_callback:
                    # Scale extraction progress to 0% - 25% of the overall process
                    progress_callback(percent * 0.25, "Extracting audio...")

            success = extract_audio_to_wav(input_path, temp_wav_path, extraction_callback)
            if not success or not os.path.exists(temp_wav_path):
                raise RuntimeError("Failed to extract audio from video.")

            # Step 2: Initialize Whisper Model (25% to 30% of progress)
            if progress_callback:
                progress_callback(25.0, "Loading speech recognition model...")
            
            logger.info(f"Loading Whisper model ({self.model_size}) for batch processing...")
            try:
                # Prioritize loading from local cache to run 100% offline with zero network requests
                model = WhisperModel(
                    self.model_size, 
                    device=self.device, 
                    compute_type=self.compute_type,
                    local_files_only=True
                )
            except Exception as e:
                logger.info(f"Local Whisper model not found ({e}). Downloading from Hugging Face...")
                model = WhisperModel(
                    self.model_size, 
                    device=self.device, 
                    compute_type=self.compute_type,
                    local_files_only=False
                )
            
            if progress_callback:
                progress_callback(30.0, "Transcribing speech...")

            # Step 3: Transcription & Translation (30% to 100% of progress)
            logger.info("Starting Whisper batch transcription...")
            segments, info = model.transcribe(temp_wav_path, beam_size=5)
            total_duration = info.duration if info else None

            # Open output file for writing (force UTF-8)
            with open(output_path, "w", encoding="utf-8") as f:
                if output_format == "vtt":
                    f.write("WEBVTT\n\n")

                item_count = 1
                for segment in segments:
                    # Translate if requested
                    text = segment.text.strip()
                    
                    if output_mode == "vi":
                        # Translate to Vietnamese only
                        translator = self._get_translator()
                        vi_text = translator.translate(text)
                        display_text = vi_text
                    elif output_mode == "dual":
                        # English + Vietnamese
                        translator = self._get_translator()
                        vi_text = translator.translate(text)
                        display_text = f"{text}\n{vi_text}"
                    else:
                        # English only
                        display_text = text

                    # Format Timestamps
                    start_str = format_timestamp(segment.start, is_vtt=(output_format == "vtt"))
                    end_str = format_timestamp(segment.end, is_vtt=(output_format == "vtt"))

                    # Write SRT/VTT entry
                    f.write(f"{item_count}\n")
                    f.write(f"{start_str} --> {end_str}\n")
                    f.write(f"{display_text}\n\n")
                    
                    item_count += 1

                    # Update progress (scaled from 30% to 95%)
                    if progress_callback and total_duration:
                        transcribe_progress = min(99.0, (segment.end / total_duration) * 100.0)
                        overall_progress = 30.0 + (transcribe_progress * 0.65)
                        progress_callback(overall_progress, f"Transcribing... ({int(transcribe_progress)}%)")

            # Finalize progress
            if progress_callback:
                progress_callback(100.0, "Export completed successfully!")

            logger.info(f"Subtitles file created: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            if progress_callback:
                progress_callback(-1.0, f"Error: {e}")
            return None

        finally:
            # Clean up temporary WAV file
            if temp_wav_path and os.path.exists(temp_wav_path):
                try:
                    os.remove(temp_wav_path)
                    logger.info("Temporary audio file cleaned up.")
                except Exception as e:
                    logger.warning(f"Failed to delete temporary audio file: {e}")
