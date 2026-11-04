"""Fireworks AI Adapter for InnerOS.

Provides an OpenAI-compatible interface to Fireworks AI inference endpoints.
Targets Meta open models (e.g. Llama 3.3 70B, Llama 3.1 8B).
Strictly governed by financial limits, zero automatic retries, and explicit owner approval.
"""
from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from copy import deepcopy
from typing import Any

from inneros_meta_guardian.provider_finance import (
    FinancialGovernanceError,
    ProviderFinanceManager,
)

FIREWORKS_DEFAULT_BASE_URL = "https://api.fireworks.ai/inference/v1"
FIREWORKS_MODELS = {
    "accounts/fireworks/models/llama-v3p3-70b-instruct": {
        "name": "Llama 3.3 70B Instruct (Meta Open Weights)",
        "input_cost_per_million": 0.90,
        "output_cost_per_million": 0.90,
        "context_window": 131072,
    },
    "accounts/fireworks/models/llama-v3p1-8b-instruct": {
        "name": "Llama 3.1 8B Instruct (Meta Open Weights)",
        "input_cost_per_million": 0.20,
        "output_cost_per_million": 0.20,
        "context_window": 131072,
    },
}


class FireworksError(Exception):
    """Raised when a Fireworks operation fails or is denied."""
    pass


class FireworksAdapter:
    """Governed client for Fireworks AI inference."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = FIREWORKS_DEFAULT_BASE_URL,
        finance_manager: ProviderFinanceManager | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("FIREWORKS_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.finance = finance_manager or ProviderFinanceManager()

    def get_supported_models(self) -> dict[str, Any]:
        return deepcopy(FIREWORKS_MODELS)

    def estimate_cost(self, model_id: str, prompt_tokens: int, max_completion_tokens: int) -> float:
        model_info = FIREWORKS_MODELS.get(model_id)
        if not model_info:
            # Fallback conservative estimate ($1.00 / 1M)
            inp_rate = 1.00
            out_rate = 1.00
        else:
            inp_rate = model_info["input_cost_per_million"]
            out_rate = model_info["output_cost_per_million"]

        est = (prompt_tokens / 1_000_000.0) * inp_rate + (max_completion_tokens / 1_000_000.0) * out_rate
        return round(est, 6)

    def complete(
        self,
        messages: list[dict[str, str]],
        model: str = "accounts/fireworks/models/llama-v3p1-8b-instruct",
        max_tokens: int = 1024,
        temperature: float = 0.2,
        owner_grant_token: str | None = None,
        mock_response: dict[str, Any] | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Executes a chat completion with Fireworks AI under strict financial governance."""
        if not messages:
            raise FireworksError("INVALID_PAYLOAD: messages list cannot be empty.")

        # Estimate prompt tokens roughly (4 chars ~ 1 token)
        raw_prompt = json.dumps(messages)
        prompt_tokens_est = max(1, len(raw_prompt) // 4)
        est_cost = self.estimate_cost(model, prompt_tokens_est, max_tokens)

        # 1. Offline mock verification
        if mock_response is not None:
            prompt_tokens = mock_response.get("usage", {}).get("prompt_tokens", prompt_tokens_est)
            comp_tokens = mock_response.get("usage", {}).get("completion_tokens", 150)
            actual_cost = self.estimate_cost(model, prompt_tokens, comp_tokens)
            receipt = self.finance.record_usage_receipt(
                provider_id="fireworks_ai",
                actual_cost_usd=actual_cost,
                prompt_tokens=prompt_tokens,
                completion_tokens=comp_tokens,
                call_type="mock_contract_verification",
            )
            return {
                "ok": True,
                "status": "MOCK_CONTRACT_VERIFIED",
                "model": model,
                "response": mock_response,
                "receipt": receipt,
            }

        # 2. Dry-run mode
        if dry_run:
            return {
                "ok": True,
                "status": "DRY_RUN_CONTRACT_VALID",
                "model": model,
                "estimated_prompt_tokens": prompt_tokens_est,
                "max_completion_tokens": max_tokens,
                "estimated_cost_usd": est_cost,
                "endpoint": f"{self.base_url}/chat/completions",
                "requires_grant": True,
            }

        # 3. Financial Pre-Call Check
        try:
            self.finance.validate_pre_call(
                provider_id="fireworks_ai",
                estimated_cost_usd=est_cost,
                owner_grant_token=owner_grant_token,
                requested_tokens=max_tokens,
            )
        except FinancialGovernanceError as e:
            raise FireworksError(f"FIREWORKS_GOVERNANCE_BLOCKED: {e}") from e

        # 4. Check API Key
        if not self.api_key:
            raise FireworksError("FIREWORKS_CREDENTIALS_MISSING: FIREWORKS_API_KEY not configured in vault/env.")

        # 5. Live Call (Zero automatic retries)
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "InnerOS-Meta-Guardian/1.2.0 (FireworksAdapter)",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise FireworksError(f"FIREWORKS_HTTP_ERROR_{e.code}: {err_body}") from e
        except Exception as e:
            raise FireworksError(f"FIREWORKS_NETWORK_FAILURE: {e}") from e

        # 6. Usage & Financial Record
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", prompt_tokens_est)
        comp_tokens = usage.get("completion_tokens", 0)
        actual_cost = self.estimate_cost(model, prompt_tokens, comp_tokens)

        receipt = self.finance.record_usage_receipt(
            provider_id="fireworks_ai",
            actual_cost_usd=actual_cost,
            prompt_tokens=prompt_tokens,
            completion_tokens=comp_tokens,
            call_type="live_inference",
        )

        return {
            "ok": True,
            "status": "LIVE_INFERENCE_SUCCESS",
            "model": model,
            "response": data,
            "receipt": receipt,
        }
