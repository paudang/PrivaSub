import sys
import os
import time

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from audio import AudioCapture
from transcriber import Transcriber

def main():
    print("==================================================")
    print("PrivaSub - Offline Whisper STT & VAD Test")
    print("==================================================")
    print("Initializing Whisper Model...")
    print("NOTE: On the first run, this will download the ~75MB 'tiny.en' model. Please wait...")
    
    try:
        # Initialize transcriber on CPU with INT8 quantization for optimal speed
        transcriber = Transcriber(model_size="tiny.en", device="cpu", compute_type="int8")
    except Exception as e:
        print(f"Error loading model: {e}")
        return
        
    print("\nWhisper model ready.")
    
    capture = AudioCapture(chunk_duration_ms=100)
    capture.start()
    
    # Wait for audio stream to stabilize
    time.sleep(0.5)
    
    print("\n--- Listening to System Audio ---")
    print(">>> Play an English video or speak in Zoom now! <<<")
    print("Press Ctrl+C to stop.\n")
    
    try:
        while True:
            # Retrieve processed audio chunks from capture queue
            chunk = capture.get_audio_chunk()
            if chunk is not None and len(chunk) > 0:
                # Send chunk to rolling buffer + VAD + Whisper transcriber
                result = transcriber.process_audio(chunk)
                if result:
                    text, is_final = result
                    tag = "  [FINAL] " if is_final else "[INTERIM] "
                    print(f"{tag}{text}")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        capture.stop()
        print("Test stopped.")

if __name__ == "__main__":
    main()
