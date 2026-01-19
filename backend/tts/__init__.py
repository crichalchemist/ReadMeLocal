"""TTS service module."""
from backend.tts.google_tts import synthesize_speech, get_cache_key

__all__ = ["synthesize_speech", "get_cache_key"]
