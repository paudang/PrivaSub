import sys
import os
import time
import numpy as np

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from audio import AudioCapture

def main():
    print("==================================================")
    print("PrivaSub - Audio Capture WASAPI Loopback Test")
    print("==================================================")
    print("Initializing audio capture...")
    
    capture = AudioCapture(chunk_duration_ms=200)
    capture.start()
    
    # Wait a moment for the stream to initialize
    time.sleep(0.5)
    
    print("\n--- Capturing system audio for 7 seconds ---")
    print(">>> Play a video, music, or speak in Zoom to test! <<<\n")
    
    start_time = time.time()
    try:
        while time.time() - start_time < 7.0:
            chunk = capture.get_audio_chunk()
            if chunk is not None and len(chunk) > 0:
                # Calculate Root-Mean-Square (RMS) amplitude
                rms = np.sqrt(np.mean(chunk**2))
                # Build a simple ASCII visual volume bar
                bar_length = min(50, int(rms * 100))
                bar = "#" * bar_length
                print(f"[{time.strftime('%H:%M:%S')}] RMS: {rms:.5f} | {bar}")
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        print("\nStopping audio capture...")
        capture.stop()
        print("Audio capture test finished.")

if __name__ == "__main__":
    main()
