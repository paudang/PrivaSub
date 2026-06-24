# Introduction

**PrivaSub** is a desktop utility that listens to your system audio (speakers or headphones) and transcribes spoken English audio, translating it on-the-fly into 10 major world languages (Vietnamese, Japanese, Chinese, Korean, Spanish, French, German, Russian, Thai), and displaying subtitles on a floating overlay window—completely offline.

## Why PrivaSub?

Many translation and transcription utilities rely on cloud-based speech-to-text APIs (like Google Cloud Speech-to-Text or OpenAI Whisper API). While accurate, this presents several problems:
1.  **Privacy Concerns:** Recording your system output means sending Zoom meetings, private video calls, and corporate conversations to third-party servers.
2.  **Cost:** Cloud APIs charge per minute of transcription, which gets expensive quickly for daily use.
3.  **Internet Dependence:** You cannot use cloud-based tools if you are offline, on a flight, or in a secure network environment.

PrivaSub solves all these problems by running **entirely offline** on your computer. It utilizes C++ optimized local neural networks that run efficiently on standard CPU hardware.

## How it works

1.  **Audio Capture:** The app hooks into Windows' native WASAPI loopback, listening to whatever is playing through your default speakers (YouTube, Zoom, Teams, VLC).
2.  **Voice Activity Detection (VAD):** The audio stream is filtered through Silero VAD. If there is only background noise, music, or silence, processing stops immediately.
3.  **Local Inference:** When speech is detected, the audio chunk is transcribed locally by `faster-whisper` (OpenAI's Whisper engine optimized with CTranslate2).
4.  **Offline Translation:** The transcribed English text is immediately translated locally into your chosen target language using an optimized Meta NLLB-200 model.
5.  **UI Render:** The original text and the translated text are rendered seamlessly in a transparent, click-through subtitle overlay window.
