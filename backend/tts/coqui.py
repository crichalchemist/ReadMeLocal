"""
Coqui TTS service wrapper.

Provides a thin abstraction to lazily load the model once and synthesize audio files on demand.
"""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Dict, Optional


class CoquiTTSService:
    """Manage a single Coqui TTS model instance."""

    def __init__(
        self,
        *,
        model_name: str,
        vocoder_path: Optional[str] = None,
        default_speaker: Optional[str] = None,
        default_language: Optional[str] = None,
        use_gpu: bool = False,
        progress_bar: bool = False,
    ) -> None:
        self.model_name = model_name
        self.vocoder_path = vocoder_path
        self.default_speaker = default_speaker
        self.default_language = default_language
        self.use_gpu = use_gpu
        self.progress_bar = progress_bar

        self._tts = None
        self._load_lock = threading.Lock()

    def _load(self):
        """Load the Coqui model lazily."""
        if self._tts is not None:
            return self._tts

        with self._load_lock:
            if self._tts is None:
                try:
                    from TTS.api import TTS  # type: ignore
                except ImportError as exc:  # pragma: no cover - runtime guard
                    raise RuntimeError("Coqui TTS is not installed. Run `pip install TTS`.") from exc

                self._tts = TTS(
                    model_name=self.model_name,
                    vocoder_path=self.vocoder_path,
                    gpu=self.use_gpu,
                    progress_bar=self.progress_bar,
                )
        return self._tts

    def synthesize_to_file(
        self,
        *,
        text: str,
        output_path: Path,
        speaker: Optional[str] = None,
        language: Optional[str] = None,
        style_wav: Optional[str] = None,
        **kwargs: Any,
    ) -> Path:
        """Render text to a file using Coqui."""
        if not text.strip():
            raise ValueError("Text is empty.")

        tts = self._load()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Merge defaults with overrides
        speaker_id = speaker or self.default_speaker
        language_id = language or self.default_language

        tts_kwargs: Dict[str, Any] = dict(kwargs)
        if speaker_id:
            tts_kwargs["speaker"] = speaker_id
        if language_id:
            tts_kwargs["language"] = language_id
        if style_wav:
            tts_kwargs["style_wav"] = style_wav

        tts.tts_to_file(text=text, file_path=str(output_path), **tts_kwargs)
        return output_path


__all__ = ["CoquiTTSService"]
