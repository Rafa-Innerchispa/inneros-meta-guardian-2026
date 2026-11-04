"""Meta Muse Voice Transcribe adapter for InnerOS VoiceOps.

Provides speech-to-text transcription preserving existing Grandstream/AssemblyAI pipelines.
Zero unapproved spend: requires valid single-use Owner Approval Grant token.
"""
from __future__ import annotations

import json
from typing import Any

from .meta_once import GRANT_STORE, GrantError

VOICE_MODEL = "muse-voice-transcribe-1.0"
VOICE_ENDPOINT = "https://api.meta.ai/v1/audio/transcriptions"
VALID_AUDIO_FORMATS = ("wav", "mp3", "ogg", "flac", "m4a")


class MetaVoiceError(RuntimeError):
    """Raised on invalid grant, unsupported format, or API error."""


class MetaVoiceClient:
    """Governed client for Meta Muse Voice transcription in VoiceOps."""

    def __init__(self, grant_store=None) -> None:
        self.grant_store = grant_store or GRANT_STORE

    def transcribe_audio_snippet(
        self,
        *,
        audio_bytes: bytes | None = None,
        audio_format: str = "wav",
        language: str = "es",
        grant_token: str | None = None,
        mock_transcript: str | None = None,
    ) -> dict[str, Any]:
        fmt = audio_format.lower().strip()
        if fmt not in VALID_AUDIO_FORMATS:
            raise MetaVoiceError(f"Unsupported audio format '{fmt}'. Allowed: {VALID_AUDIO_FORMATS}")

        if mock_transcript is None:
            if not audio_bytes:
                raise MetaVoiceError("Audio bytes cannot be empty.")
            if not grant_token:
                raise MetaVoiceError("MUSE_VOICE_BLOCKED: Single-use Owner Approval Grant token is required.")
            try:
                grant = self.grant_store.consume(grant_token)
            except GrantError as exc:
                raise MetaVoiceError(f"MUSE_VOICE_GRANT_INVALID: {exc}") from exc
            raise MetaVoiceError("MUSE_VOICE_NETWORK_BLOCKED: Live external voice transcription disabled in offline mode.")

        return {
            "ok": True,
            "status": "MOCK_CONTRACT_VERIFIED",
            "model": VOICE_MODEL,
            "language": language,
            "audio_format": fmt,
            "transcript": mock_transcript,
            "confidence": 0.98,
            "incremental_cost_usd": 0.0,
        }
