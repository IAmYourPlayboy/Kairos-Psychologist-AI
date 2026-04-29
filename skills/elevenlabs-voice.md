---
name: elevenlabs-voice
description: "Skill for integrating ElevenLabs API into AI-Психолог. Covers text-to-speech generation, Professional Voice Cloning (PVC) for the Digital Twin module, emotion control in synthesized speech, Russian language support, and voice pipeline architecture. Use when working with ElevenLabs API calls, voice cloning from family audio, TTS for breathing exercises, or designing the voice interface. Also trigger for Whisper/Golos STT integration and audio emotion analysis pipeline with Aniemore."
---

# ElevenLabs Voice Integration

## Role in the System
Voice serves THREE distinct purposes:
1. **Digital Twin**: Clone deceased person's voice from family-provided audio (PVC)
2. **Emotion Analysis Input**: Capture user's voice → Aniemore SER → distress assessment
3. **Optional TTS Output**: Breathing exercise guidance, grounding instructions

**CRITICAL**: In crisis mode (PFA), TEXT input is preferred over voice. Typing grounds the user (activates prefrontal cortex). Voice output is optional — offer as choice, never force.

## ElevenLabs API Integration

### Text-to-Speech (Basic)
```python
import requests

def generate_speech(text, voice_id, api_key, stability=0.7, similarity=0.8):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": stability, "similarity_boost": similarity}
    }
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        return response.content
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            # Rate limited — wait and retry
            raise Exception("ElevenLabs rate limit hit, retry after cooldown")
        raise
    except requests.exceptions.Timeout:
        raise Exception("ElevenLabs request timed out")
```

### Professional Voice Cloning (Digital Twin)
Requirements: Several minutes of clean audio from the deceased.
Sources: voice messages, video recordings, phone calls.
Recording quality tips: peaks at -6dB to -3dB, ~20cm from microphone.

The cloned voice becomes the Digital Twin's voice output. Combined with personality profile system prompt, it creates the transitional object experience.

### Emotion Control in TTS
ElevenLabs supports emotional expression through:
- Stability parameter (lower = more emotional variation)
- SSML-like tags for pauses: `<break time="2s" />`
- Text emphasis for prosody: "This is IMPORTANT"
- Natural phrasing for sadness vs calm vs warmth

For Digital Twin fade-out phase: gradually increase stability (voice becomes calmer, more distant).
```
Fade-out voice parameter schedule:
Phase 1 (Active):      stability=0.5, similarity_boost=0.8  (warm, expressive)
Phase 2 (Early fade):  stability=0.6, similarity_boost=0.7  (calmer)
Phase 3 (Mid fade):    stability=0.7, similarity_boost=0.6  (reflective, distant)
Phase 4 (Final):       stability=0.9, similarity_boost=0.5  (peaceful, fading)
```

## STT Pipeline (Input)
- **Whisper** (OpenAI): Open-source, excellent Russian support
- **Golos** (Salute/SberDevices): Russian-specific ASR
- Pipeline: User audio → Whisper STT → text → LLM + parallel → Aniemore SER → emotion score

## Audio Emotion Analysis
- User voice → Aniemore VoiceRecognizer (WavLM model)
- Output: emotion probabilities across 7 categories
- Feed into Layer 1 of NLP analysis as additional distress signal
- Prosodic markers: monotone voice, reduced tempo → shutdown indicators

## Privacy & Legal
- ElevenLabs processes audio on their servers — potential FZ-152 conflict
- Solution: Use ElevenLabs only for TTS output (not for user data processing)
- User voice analysis: process locally with Aniemore (self-hosted)
- Voice cloning consent: obtained from living relatives of the deceased
