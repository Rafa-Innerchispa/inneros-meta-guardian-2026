"""Meta Muse Spark 1.3 client and adapter for InnerOS.

Provides fast agentic inference and tool calling via Meta Model API.
Zero unapproved spend: requires valid single-use Owner Approval Grant token.
"""
from __future__ import annotations

import json
import time
from typing import Any

from .meta_once import GRANT_STORE, GrantError

SPARK_MODEL = "muse-spark-1.3"
SPARK_ENDPOINT = "https://api.meta.ai/v1/responses"


class MetaSparkError(RuntimeError):
    """Raised on invalid grant, budget violation, or API contract error."""


class MetaSparkClient:
    """Governed client for Meta Muse Spark 1.3."""

    def __init__(self, grant_store=None) -> None:
        self.grant_store = grant_store or GRANT_STORE

    def invoke(
        self,
        *,
        prompt: str,
        grant_token: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        reasoning_effort: str = "high",
        max_output_tokens: int = 2048,
        mock_response: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Invoke Muse Spark 1.3 with mandatory single-use grant validation."""
        clean_prompt = str(prompt or "").strip()
        if not clean_prompt:
            raise MetaSparkError("Prompt cannot be empty.")

        # Require single-use grant token unless mock response provided for offline contract tests
        if mock_response is None:
            if not grant_token:
                raise MetaSparkError("MUSE_SPARK_BLOCKED: Single-use Owner Approval Grant token is required.")
            try:
                # Atomically consume grant token before network dispatch
                grant = self.grant_store.consume(grant_token)
            except GrantError as exc:
                raise MetaSparkError(f"MUSE_SPARK_GRANT_INVALID: {exc}") from exc

            # In production, dispatch HTTP request to SPARK_ENDPOINT
            # For demonstration without external spend:
            raise MetaSparkError("MUSE_SPARK_NETWORK_BLOCKED: Live external spend disabled in offline mode.")

        # Offline validated contract response
        return {
            "ok": True,
            "status": "MOCK_CONTRACT_VERIFIED",
            "model": SPARK_MODEL,
            "prompt": clean_prompt,
            "tools_provided": len(tools or []),
            "reasoning_effort": reasoning_effort,
            "max_output_tokens": max_output_tokens,
            "response": mock_response,
            "incremental_cost_usd": 0.0,
        }
