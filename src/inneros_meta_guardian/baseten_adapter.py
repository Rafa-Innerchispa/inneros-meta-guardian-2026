"""Baseten Model APIs and Tool Calls Adapter for InnerOS.

Provides an OpenAI-compatible interface to Baseten Serverless Model APIs and Tool Calls.
Strictly separates:
- Model APIs credits ($5.00 free tier)
- Tool Calls credits ($2.00 free tier)
- Dedicated Inference is $0.00 (disabled, requires credit card)
Fail-closed without valid API key and Owner Approval Grant.
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

BASETEN_DEFAULT_BASE_URL = "https://inference.baseten.co/v1"
BASETEN_MODELS = {
    "meta-models/muse-spark-open": {
        "name": "Meta Muse Spark Open (Serverless)",
        "input_cost_per_million": 0.50,
        "output_cost_per_million": 1.50,
        "pool": "model_apis",
    },
    "meta-llama/Llama-3.1-8B-Instruct": {
        "name": "Llama 3.1 8B Instruct (Serverless Baseten)",
        "input_cost_per_million": 0.30,
        "output_cost_per_million": 0.60,
        "pool": "model_apis",
    },
}


class BasetenError(Exception):
    """Raised when a Baseten operation fails or is denied."""
    pass


class BasetenAdapter:
    """Governed client for Baseten Model APIs and Tool Calls."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = BASETEN_DEFAULT_BASE_URL,
        finance_manager: ProviderFinanceManager | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("BASETEN_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.finance = finance_manager or ProviderFinanceManager()

    def get_supported_models(self) -> dict[str, Any]:
        return deepcopy(BASETEN_MODELS)

    def estimate_cost(self, model_id: str, prompt_tokens: int, max_completion_tokens: int) -> float:
        model_info = BASETEN_MODELS.get(model_id, {})
        inp_rate = model_info.get("input_cost_per_million", 0.50)
        out_rate = model_info.get("output_cost_per_million", 1.50)
        est = (prompt_tokens / 1_000_000.0) * inp_rate + (max_completion_tokens / 1_000_000.0) * out_rate
        return round(est, 6)

    def complete(
        self,
        messages: list[dict[str, str]],
        model: str = "meta-models/muse-spark-open",
        max_tokens: int = 1024,
        temperature: float = 0.2,
        is_tool_call: bool = False,
        owner_grant_token: str | None = None,
        mock_response: dict[str, Any] | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Executes a completion on Baseten under separate credit pool governance."""
        if not messages:
            raise BasetenError("INVALID_PAYLOAD: messages list cannot be empty.")

        pool_name = "tool_calls_available_usd" if is_tool_call else "primary"
        raw_prompt = json.dumps(messages)
        prompt_tokens_est = max(1, len(raw_prompt) // 4)
        est_cost = self.estimate_cost(model, prompt_tokens_est, max_tokens)

        # 1. Mock contract verification
        if mock_response is not None:
            prompt_tokens = mock_response.get("usage", {}).get("prompt_tokens", prompt_tokens_est)
            comp_tokens = mock_response.get("usage", {}).get("completion_tokens", 120)
            actual_cost = self.estimate_cost(model, prompt_tokens, comp_tokens)
            receipt = self.finance.record_usage_receipt(
                provider_id="baseten",
                actual_cost_usd=actual_cost,
                prompt_tokens=prompt_tokens,
                completion_tokens=comp_tokens,
                call_type="mock_contract_verification",
                pool_name=pool_name,
            )
            return {
                "ok": True,
                "status": "MOCK_CONTRACT_VERIFIED",
                "model": model,
                "pool": pool_name,
                "response": mock_response,
                "receipt": receipt,
            }

        # 2. Dry run
        if dry_run:
            return {
                "ok": True,
                "status": "DRY_RUN_CONTRACT_VALID",
                "model": model,
                "pool": pool_name,
                "estimated_prompt_tokens": prompt_tokens_est,
                "max_completion_tokens": max_tokens,
                "estimated_cost_usd": est_cost,
                "endpoint": f"{self.base_url}/chat/completions",
                "dedicated_inference_allowed": False,
            }

        # 3. Financial Pre-Call Check
        try:
            self.finance.validate_pre_call(
                provider_id="baseten",
                estimated_cost_usd=est_cost,
                owner_grant_token=owner_grant_token,
                requested_tokens=max_tokens,
            )
        except FinancialGovernanceError as e:
            raise BasetenError(f"BASETEN_GOVERNANCE_BLOCKED: {e}") from e

        # 4. Check API Key
        if not self.api_key:
            raise BasetenError("BASETEN_CREDENTIALS_MISSING: BASETEN_API_KEY not configured in vault/env.")

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
                "Authorization": f"Api-Key {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "InnerOS-Meta-Guardian/1.2.0 (BasetenAdapter)",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise BasetenError(f"BASETEN_HTTP_ERROR_{e.code}: {err_body}") from e
        except Exception as e:
            raise BasetenError(f"BASETEN_NETWORK_FAILURE: {e}") from e

        # 6. Usage & Financial Record
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", prompt_tokens_est)
        comp_tokens = usage.get("completion_tokens", 0)
        actual_cost = self.estimate_cost(model, prompt_tokens, comp_tokens)

        receipt = self.finance.record_usage_receipt(
            provider_id="baseten",
            actual_cost_usd=actual_cost,
            prompt_tokens=prompt_tokens,
            completion_tokens=comp_tokens,
            call_type="live_inference",
            pool_name=pool_name,
        )

        return {
            "ok": True,
            "status": "LIVE_INFERENCE_SUCCESS",
            "model": model,
            "pool": pool_name,
            "response": data,
            "receipt": receipt,
        }

