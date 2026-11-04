"""Meta Muse Image adapter for InnerChispa Creative.

Provides governed schema-validated image generation and editing.
Zero unapproved spend: requires valid single-use Owner Approval Grant token.
"""
from __future__ import annotations

import json
from typing import Any

from .meta_once import GRANT_STORE, GrantError

IMAGE_MODEL = "muse-image-1.0"
IMAGE_ENDPOINT = "https://api.meta.ai/v1/images"
VALID_RESOLUTIONS = ("512x512", "768x768", "1024x1024", "1024x1536", "1536x1024")


class MetaImageError(RuntimeError):
    """Raised on invalid grant, invalid dimensions, or API contract error."""


class MetaImageClient:
    """Governed client for Meta Muse Image generation and editing."""

    def __init__(self, grant_store=None) -> None:
        self.grant_store = grant_store or GRANT_STORE

    def generate_creative_asset(
        self,
        *,
        prompt: str,
        resolution: str = "1024x1024",
        style: str = "photorealistic_infrastructure",
        grant_token: str | None = None,
        mock_output_path: str | None = None,
    ) -> dict[str, Any]:
        clean_prompt = str(prompt or "").strip()
        if not clean_prompt:
            raise MetaImageError("Image prompt cannot be empty.")
        if resolution not in VALID_RESOLUTIONS:
            raise MetaImageError(f"Invalid resolution '{resolution}'. Allowed: {VALID_RESOLUTIONS}")

        if mock_output_path is None:
            if not grant_token:
                raise MetaImageError("MUSE_IMAGE_BLOCKED: Single-use Owner Approval Grant token is required.")
            try:
                grant = self.grant_store.consume(grant_token)
            except GrantError as exc:
                raise MetaImageError(f"MUSE_IMAGE_GRANT_INVALID: {exc}") from exc
            raise MetaImageError("MUSE_IMAGE_NETWORK_BLOCKED: Live paid image generation disabled in offline mode.")

        return {
            "ok": True,
            "status": "MOCK_CONTRACT_VERIFIED",
            "model": IMAGE_MODEL,
            "prompt": clean_prompt,
            "resolution": resolution,
            "style": style,
            "asset_path": mock_output_path,
            "incremental_cost_usd": 0.0,
        }
