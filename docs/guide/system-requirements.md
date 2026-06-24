# System Requirements

To ensure smooth, real-time audio capture, transcription, and bi-directional translation (English ↔ Vietnamese) using advanced on-premise AI models like Whisper and Meta NLLB-200, your machine should meet the following specifications.

---

## Minimum Specifications
*Designed for standard 720p/1080p video playback or Zoom meetings with PrivaSub active.*

*   **Operating System:** Windows 10 / 11 (64-bit required for native WASAPI loopback audio capture).
*   **Processor (CPU):** Intel Core i3 (8th Gen or newer) or AMD Ryzen 3 (Minimum 4 cores / 4 threads). **Note:** AVX2 instruction set support is required for CTranslate2 CPU acceleration.
*   **Memory (RAM):** 8 GB RAM. *(PrivaSub consumes approximately 1.2 GB – 1.5 GB of RAM when running both Whisper tiny and NLLB-200 INT8 models in memory).*
*   **Storage:** 1.5 GB of free disk space (to store Python virtual environment packages, Whisper models, and NLLB-200 weights).
*   **Python:** Version 3.8 to 3.12 (64-bit).

---

## Recommended Specifications
*Designed for flawless 60 FPS UI rendering, ultra-low latency live translation, and heavy multitasking (e.g., hosting 4K YouTube streams or large Zoom conferences).*

*   **Operating System:** Windows 10 / 11 (64-bit).
*   **Processor (CPU):** Intel Core i5 / i7 (10th Gen or newer) or AMD Ryzen 5 / 7 (6 cores / 12 threads or higher).
*   **Memory (RAM):** 16 GB RAM (ensures seamless background execution alongside resource-heavy web browsers and video conferencing tools).
*   **Storage:** SSD with 2 GB free space (SSD ensures instantaneous model loading in <2 seconds upon launch).
*   **Graphics (GPU):** While PrivaSub is heavily optimized to run entirely on CPU using INT8 quantization, having a dedicated GPU helps free up CPU resources for video decoding.

---

## Hardware Efficiency & AI Models

PrivaSub achieves state-of-the-art translation accuracy without requiring high-end server hardware by utilizing advanced **INT8 Quantization** via CTranslate2:

1.  **Whisper Multilingual (`tiny`):** Consumes ~150 MB RAM. Operates with extremely fast real-time factor (RTF) for audio transcription.
2.  **Meta NLLB-200 (`nllb-200-distilled-600M`):** Highly optimized 600M parameter model compressed to 8-bit integers. Consumes ~600 MB storage and ~500 MB RAM, delivering premium bilingual contextual accuracy while keeping your data 100% offline.
