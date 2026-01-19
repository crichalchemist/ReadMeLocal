"""
Google Cloud Text-to-Speech service wrapper.

Provides synthesis using Google Cloud TTS API with caching support.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any, Optional


class GoogleTTSService:
    """Manage Google Cloud TTS synthesis."""

    def __init__(
        self,
        *,
        default_voice: str = "en-US-Neural2-D",
        default_speaking_rate: float = 1.0,
        default_pitch: float = 0.0,
        audio_encoding: str = "MP3",
    ) -> None:
        self.default_voice = default_voice
        self.default_speaking_rate = default_speaking_rate
        self.default_pitch = default_pitch
        self.audio_encoding = audio_encoding
        self._client = None

    def _get_client(self):
        """Lazy-load the Google TTS client."""
        if self._client is not None:
            return self._client

        try:
            from google.cloud import texttospeech
        except ImportError as exc:
            raise RuntimeError(
                "google-cloud-texttospeech is not installed. "
                "Run `pip install google-cloud-texttospeech`."
            ) from exc

        self._client = texttospeech.TextToSpeechClient()
        return self._client

    def synthesize_to_file(
        self,
        *,
        text: str,
        output_path: Path,
        speaker: Optional[str] = None,
        language: Optional[str] = None,
        speaking_rate: Optional[float] = None,
        pitch: Optional[float] = None,
        **kwargs: Any,
    ) -> Path:
        """
        Synthesize text to an audio file using Google Cloud TTS.

        Args:
            text: Text to synthesize (plain text or SSML)
            output_path: Path to write the audio file
            speaker: Voice name (e.g., "en-US-Neural2-D"). Overrides default.
            language: Language code (e.g., "en-US"). Extracted from voice if not provided.
            speaking_rate: Speed multiplier (0.25 to 4.0). Default 1.0.
            pitch: Pitch adjustment in semitones (-20.0 to 20.0). Default 0.0.

        Returns:
            Path to the generated audio file.
        """
        if not text.strip():
            raise ValueError("Text is empty.")

        from google.cloud import texttospeech

        client = self._get_client()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Determine voice name
        voice_name = speaker or self.default_voice

        # Extract language code from voice name if not provided
        # Voice names follow pattern: "en-US-Neural2-D" -> language_code = "en-US"
        if language:
            language_code = language
        else:
            parts = voice_name.split("-")
            language_code = "-".join(parts[:2]) if len(parts) >= 2 else "en-US"

        # Detect SSML vs plain text
        if text.strip().startswith("<speak>"):
            synthesis_input = texttospeech.SynthesisInput(ssml=text)
        else:
            synthesis_input = texttospeech.SynthesisInput(text=text)

        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_name,
        )

        # Determine audio encoding and file extension
        encoding_map = {
            "MP3": texttospeech.AudioEncoding.MP3,
            "LINEAR16": texttospeech.AudioEncoding.LINEAR16,
            "OGG_OPUS": texttospeech.AudioEncoding.OGG_OPUS,
        }
        encoding = encoding_map.get(self.audio_encoding, texttospeech.AudioEncoding.MP3)

        audio_config = texttospeech.AudioConfig(
            audio_encoding=encoding,
            speaking_rate=speaking_rate or self.default_speaking_rate,
            pitch=pitch or self.default_pitch,
        )

        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config,
        )

        # Write audio content to file
        # Adjust extension based on encoding
        ext_map = {"MP3": ".mp3", "LINEAR16": ".wav", "OGG_OPUS": ".ogg"}
        expected_ext = ext_map.get(self.audio_encoding, ".mp3")

        # If output_path has different extension, adjust it
        if output_path.suffix.lower() != expected_ext:
            output_path = output_path.with_suffix(expected_ext)

        output_path.write_bytes(response.audio_content)
        return output_path

    @staticmethod
    def get_cache_key(text: str, voice: str, rate: float) -> str:
        """Generate a cache key for audio content."""
        content = f"{text}:{voice}:{rate}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


__all__ = ["GoogleTTSService"]
