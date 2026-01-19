"""
Google Cloud Text-to-Speech service wrapper.

Provides synthesis with caching and SSML support.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

from google.cloud import texttospeech


def get_cache_key(text: str, voice: str, rate: float) -> str:
    """Generate cache key for audio based on text, voice, and rate."""
    content = f"{text}:{voice}:{rate}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def synthesize_speech(
    text: str,
    voice_name: str = "en-US-Neural2-D",
    speaking_rate: float = 1.0,
    pitch: float = 0.0,
    audio_encoding: str = "MP3",
) -> bytes:
    """
    Synthesize speech using Google Cloud TTS.

    Args:
        text: Text to synthesize (plain text or SSML)
        voice_name: Google voice name (e.g., "en-US-Neural2-D")
        speaking_rate: Speed multiplier (0.25 to 4.0)
        pitch: Pitch adjustment in semitones (-20.0 to 20.0)
        audio_encoding: "MP3" or "LINEAR16" (WAV)

    Returns:
        Audio bytes

    Raises:
        google.api_core.exceptions.GoogleAPIError: On API failure
        ValueError: On invalid parameters
    """
    client = texttospeech.TextToSpeechClient()

    # Detect SSML vs plain text
    if text.strip().startswith("<speak>"):
        synthesis_input = texttospeech.SynthesisInput(ssml=text)
    else:
        synthesis_input = texttospeech.SynthesisInput(text=text)

    # Parse language code from voice name (e.g., "en-US-Neural2-D" -> "en-US")
    parts = voice_name.split("-")
    language_code = "-".join(parts[:2]) if len(parts) >= 2 else "en-US"

    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        name=voice_name,
    )

    # Map encoding string to enum
    encoding_map = {
        "MP3": texttospeech.AudioEncoding.MP3,
        "LINEAR16": texttospeech.AudioEncoding.LINEAR16,
        "OGG_OPUS": texttospeech.AudioEncoding.OGG_OPUS,
    }
    encoding = encoding_map.get(audio_encoding.upper(), texttospeech.AudioEncoding.MP3)

    audio_config = texttospeech.AudioConfig(
        audio_encoding=encoding,
        speaking_rate=speaking_rate,
        pitch=pitch,
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
    )

    return response.audio_content


__all__ = ["synthesize_speech", "get_cache_key"]
