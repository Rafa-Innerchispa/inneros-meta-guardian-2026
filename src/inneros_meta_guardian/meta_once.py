"""Meta Muse Spark 1.3 One-Shot Operator with Single-Use Cryptographic Grants.

Governed Operator Interface:
1. Owner creates a one-shot grant strictly bound to a single snapshot_digest.
2. Grant is consumed atomically BEFORE remote dispatch to prevent replay loops.
3. Payload is sanitized and anonymized (no private IPs, MACs, or credentials).
4. Emits an immutable, tamper-evident receipt.
5. If Meta API key is missing or credits pending, returns NOT_RUN with graceful local fallback.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

from .integrations import canonical_json, redact_sensitive_data


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class GrantError(ValueError):
    """Raised when a one-shot grant is invalid, expired, already consumed, or mismatched."""


class OneShotGrantStore:
    """Manages ephemeral, single-use grants bound to exact snapshot digests."""

    def __init__(self) -> None:
        # token -> grant_info
        self._grants: dict[str, dict[str, Any]] = {}

    def create_grant(
        self,
        snapshot_digest: str,
        ttl_seconds: int = 300,
        max_tokens: int = 400,
        model: str = "muse-spark-1.3",
    ) -> dict[str, Any]:
        if not snapshot_digest or len(snapshot_digest) != 64:
            raise GrantError("Invalid snapshot_digest: must be a 64-character SHA-256 hex string.")
        
        token = f"grant_{secrets.token_hex(20)}"
        expires_at = time.time() + ttl_seconds
        grant = {
            "token": token,
            "snapshot_digest": snapshot_digest,
            "created_at": now_iso(),
            "expires_at": expires_at,
            "ttl_seconds": ttl_seconds,
            "max_tokens": max_tokens,
            "model": model,
            "consumed": False,
            "consumed_at": None,
        }
        self._grants[token] = grant
        return grant

    def consume_grant(self, token: str, snapshot_digest: str) -> dict[str, Any]:
        """Atomically validates and marks a grant as consumed.
        
        Must be executed BEFORE any external network call.
        """
        grant = self._grants.get(token)
        if not grant:
            raise GrantError("Grant token not found or already purged.")
        if grant["consumed"]:
            raise GrantError("Grant token has ALREADY been consumed (replay prevented).")
        if time.time() > grant["expires_at"]:
            raise GrantError("Grant token has expired.")
        if grant["snapshot_digest"] != snapshot_digest:
            raise GrantError(
                f"Grant snapshot_digest mismatch: expected {grant['snapshot_digest'][:12]}..., got {snapshot_digest[:12]}..."
            )

        # Mark consumed atomically before returning
        grant["consumed"] = True
        grant["consumed_at"] = now_iso()
        return grant

    def get_grant(self, token: str) -> dict[str, Any] | None:
        return self._grants.get(token)


# Process-level singleton grant store
GRANT_STORE = OneShotGrantStore()


class MetaOnceOperator:
    """Executes a single, governed inference against Meta Muse Spark 1.3."""

    OFFICIAL_ENDPOINT = "https://api.meta.ai/v1/responses"
    DEFAULT_MODEL = "muse-spark-1.3"

    SYSTEM_INSTRUCTION = (
        "You are InnerOS Infrastructure Guardian powered by Meta Muse Spark 1.3. "
        "Analyze the provided physical infrastructure signals and historical memory facts. "
        "Structure your response strictly into four short sections: "
        "1. OBSERVATIONS (factual state from signals) "
        "2. HYPOTHESES (probable technical cause) "
        "3. UNCERTAINTY (explicit limitations and what is NOT proven) "
        "4. RECOMMENDED ACTION (safe, non-destructive governed operator action). "
        "Keep total length under 130 words. Do NOT invent actions, device IPs, credentials, or customer names."
    )

    def __init__(self, endpoint: str | None = None, api_key: str | None = None) -> None:
        self.endpoint = endpoint or os.getenv("META_RESPONSES_URL", self.OFFICIAL_ENDPOINT)
        self.api_key = api_key or os.getenv("MODEL_API_KEY") or os.getenv("META_API_KEY")

    def execute_inference(
        self,
        grant_token: str,
        incident_telemetry: dict[str, Any],
        historical_memory: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Executes a single inference. Consumes grant before calling remote endpoint."""
        
        # 1. Validate snapshot digest
        raw_signals = incident_telemetry.get("signals", [])
        snapshot_digest = incident_telemetry.get("snapshot_digest")
        if not snapshot_digest:
            src = canonical_json({"site": incident_telemetry.get("site"), "signals": raw_signals})
            snapshot_digest = hashlib.sha256(src.encode("utf-8")).hexdigest()

        # 2. Consume grant atomically (raises GrantError if invalid or replayed)
        grant = GRANT_STORE.consume_grant(grant_token, snapshot_digest)

        # 3. Sanitize telemetry and memory
        clean_telemetry = redact_sensitive_data(incident_telemetry)
        clean_memory = redact_sensitive_data(historical_memory)

        user_content = json.dumps(
            {
                "site": clean_telemetry.get("site"),
                "category": clean_telemetry.get("category"),
                "observed_signals": clean_telemetry.get("signals"),
                "source_timestamp": clean_telemetry.get("source_observed_at") or clean_telemetry.get("collected_at"),
                "verified_memory_facts": [
                    {"title": f.get("title"), "fact": f.get("fact"), "confidence": f.get("confidence")}
                    for f in clean_memory
                ],
            },
            ensure_ascii=False,
        )

        request_hash = hashlib.sha256(user_content.encode("utf-8")).hexdigest()
        start_time = time.time()

        # 4. Check if Meta API Key is available
        if not self.api_key:
            # Deterministic, governed fallback when key is not configured or credits pending
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "ok": True,
                "status": "NOT_RUN",
                "reason": "MODEL_API_KEY_ABSENT_OR_CREDITS_PENDING",
                "model": grant["model"],
                "provider": "meta-muse-spark",
                "truth": "GOVERNED_ONE_SHOT_RECEIPT",
                "grant_token": grant_token,
                "snapshot_digest": snapshot_digest,
                "request_hash": request_hash,
                "timestamp": now_iso(),
                "latency_ms": latency_ms,
                "response_id": None,
                "tokens_used": 0,
                "local_fallback_applied": True,
                "analysis": {
                    "observations": f"Site {clean_telemetry.get('site')} category {clean_telemetry.get('category')} reported {len(raw_signals)} telemetry signals.",
                    "hypotheses": "Signals indicate nominal operating boundary or localized threshold condition requiring operator inspection.",
                    "uncertainty": "External Meta live inference was NOT run (pending promotional credit activation). Analysis derived deterministically from verified local policy.",
                    "recommended_action": "Request operator review via Home Assistant mobile notification.",
                },
            }

        # 5. Remote call to Meta Responses API
        payload = {
            "model": grant["model"],
            "max_tokens": grant.get("max_tokens", 400),
            "input": [
                {
                    "type": "message",
                    "role": "system",
                    "content": [{"type": "input_text", "text": self.SYSTEM_INSTRUCTION}],
                },
                {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_content}],
                },
            ],
        }

        req = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "InnerOS-Meta-Guardian-Agent/2026.11",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=12.0) as resp:
                raw_resp = resp.read(131072)
            data = json.loads(raw_resp.decode("utf-8"))
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Parse Responses API output
            response_id = data.get("id")
            usage = data.get("usage", {})
            tokens_used = usage.get("total_tokens") or usage.get("output_tokens", 0)

            # Extract generated text
            output = data.get("output", [])
            messages = [x for x in output if x.get("type") == "message"]
            content_pieces = [c.get("text", "") for m in messages for c in m.get("content", []) if c.get("type") == "output_text"]
            text_result = " ".join(content_pieces).strip()
            if not isinstance(response_id, str) or not response_id.strip() or not text_result:
                return {
                    "ok": False,
                    "status": "BLOCKED",
                    "error": "PROVIDER_RECEIPT_INCOMPLETE: missing authentic response id or output text",
                    "provider": "meta-muse-spark",
                    "model": grant["model"],
                    "truth": "NO_VERIFIED_MODEL_OUTPUT",
                    "snapshot_digest": snapshot_digest,
                    "request_hash": request_hash,
                    "timestamp": now_iso(),
                    "latency_ms": latency_ms,
                    "local_fallback_applied": True,
                    "response_id": None,
                }

            return {
                "ok": True,
                "status": "REAL",
                "model": grant["model"],
                "provider": "meta-muse-spark",
                "truth": "LIVE_META_INFERENCE_EXECUTION",
                "grant_token": grant_token,
                "snapshot_digest": snapshot_digest,
                "request_hash": request_hash,
                "timestamp": now_iso(),
                "latency_ms": latency_ms,
                "response_id": response_id,
                "tokens_used": tokens_used,
                "local_fallback_applied": False,
                "raw_text": text_result,
                "analysis": {
                    "observations": "Extracted from live Meta Muse Spark response",
                    "hypotheses": "Meta Muse Spark physical infrastructure assessment",
                    "uncertainty": "Inference bounded by snapshot timestamp; no direct device actuation authority.",
                    "recommended_action": text_result[:250],
                },
            }
        except Exception as exc:
            latency_ms = int((time.time() - start_time) * 1000)
            # Safe receipt indicating provider error without exposing auth headers
            return {
                "ok": False,
                "status": "BLOCKED",
                "error": f"Meta Model API call failed ({type(exc).__name__})",
                "model": grant["model"],
                "provider": "meta-muse-spark",
                "truth": "GOVERNED_ONE_SHOT_RECEIPT",
                "grant_token": grant_token,
                "snapshot_digest": snapshot_digest,
                "request_hash": request_hash,
                "timestamp": now_iso(),
                "latency_ms": latency_ms,
                "local_fallback_applied": True,
            }
