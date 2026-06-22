# How it Works Under the Hood

This page covers the technical architecture and pipeline behind PrivaSub.

## 1. System Audio Loopback Capture
Standard audio recording libraries only capture input devices like microphones. To capture what the computer is playing (Zoom, YouTube, etc.), PrivaSub uses Windows **WASAPI Loopback** via the `PyAudioWPatch` library.

When the application starts:
1.  It queries Windows for the default audio output device (speakers or headphones).
2.  It finds the corresponding Virtual WASAPI loopback input device.
3.  It opens an input stream at the device's **native sample rate** (typically 48000Hz or 44100Hz) and **native channels** (usually 2 channels, stereo) to prevent sample rate errors.

---

## 2. Resampling & Downmixing Pipeline
Whisper models expect audio input in a specific format: **16000Hz, Mono, 32-bit Float, normalized between -1.0 and 1.0**.

PrivaSub processes incoming raw 16-bit PCM (stereo, 48kHz) buffers in real-time:
1.  **Downmixing:** Averages the left and right audio channels to convert stereo to mono.
2.  **Normalization:** Converts 16-bit signed integer values (`-32768` to `32767`) to 32-bit floats (`-1.0` to `1.0`) by dividing by `32768.0`.
3.  **Resampling:** Uses a pure-numpy linear interpolator to resample the audio from 48000Hz (or native rate) to 16000Hz. This avoids heavy external dependencies like `librosa` or `scipy`.

---

## 3. Voice Activity Detection (VAD)
Running speech-to-text models continuously on CPU consumes significant processing power. To keep CPU utilization at ~0% during silence:
1.  Audio chunks (100ms) are pushed into a thread-safe Queue.
2.  PrivaSub passes the rolling accumulator buffer to **Silero VAD** (integrated into `faster-whisper`).
3.  If Silero VAD detects no speech, the Whisper inference loop is skipped, preventing CPU spikes.

---

## 4. Local Whisper Inference
When VAD detects active speech, the processed audio buffer is passed to `faster-whisper`:
*   **Engine:** Powered by `CTranslate2` (a fast C++ inference engine for Transformer models).
*   **Quantization:** Configured to `int8` on CPU. This reduces the memory usage and execution latency by 4x compared to the standard PyTorch FP32 float execution, making it highly responsive on modern laptop/desktop processors.
