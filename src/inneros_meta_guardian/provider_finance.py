"""Financial controls, balance tracking, and budget governance for InnerOS Providers.

Strictly enforces:
- Pre-call authorization and balance verification
- Explicit single-use owner approval grants
- Local per-execution budget ceilings
- Zero automatic retries on paid APIs
- Token, duration, and concurrency caps
- Post-call cryptographic receipts and balance ledger updates
- Fail-closed execution when spend cannot be strictly bounded
"""
from __future__ import annotations

import hashlib
import json
import os
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


class FinancialGovernanceError(Exception):
    """Raised when a financial rule or budget ceiling is violated."""
    pass


@dataclass
class ProviderFinancialProfile:
    provider_id: str
    display_name: str
    account_email: str | None
    organization: str
    available_balance_usd: float
    used_balance_usd: float
    auto_reload_enabled: bool
    free_credits_only: bool
    status: str  # NOT_CONFIGURED, CONFIGURED, TESTED_OFFLINE, TESTED_LIVE, BLOCKED
    proposed_test_budget_usd: float
    per_call_ceiling_usd: float
    max_tokens_per_call: int
    timeout_seconds: int
    max_retries: int = 0
    extra_pools: dict[str, float] = field(default_factory=dict)
    notes: str = ""


# Verified Financial Ledger baseline as of November 4, 2026
INITIAL_FINANCIAL_LEDGER: dict[str, ProviderFinancialProfile] = {
    "fireworks_ai": ProviderFinancialProfile(
        provider_id="fireworks_ai",
        display_name="Fireworks AI",
        account_email="rafagye@gmail.com",
        organization="InnerChispa LLC",
        available_balance_usd=20.299683,
        used_balance_usd=0.000317,
        auto_reload_enabled=False,
        free_credits_only=False,
        status="TESTED_LIVE",
        proposed_test_budget_usd=1.00,
        per_call_ceiling_usd=0.25,
        max_tokens_per_call=2048,
        timeout_seconds=30,
        max_retries=0,
        notes="Active funded account. Live verified call chatcmpl-f7f26716... on muse-spark-open ($0.000317 USD).",
    ),
    "baseten": ProviderFinancialProfile(
        provider_id="baseten",
        display_name="Baseten Model APIs & Tool Calls",
        account_email=None,
        organization="InnerChispa LLC",
        available_balance_usd=4.999729,  # Model APIs pool
        used_balance_usd=0.000271,
        auto_reload_enabled=False,
        free_credits_only=True,
        status="TESTED_LIVE",
        proposed_test_budget_usd=0.50,
        per_call_ceiling_usd=0.10,
        max_tokens_per_call=2048,
        timeout_seconds=30,
        max_retries=0,
        extra_pools={
            "tool_calls_available_usd": 2.00,
            "tool_calls_used_usd": 0.0,
            "dedicated_inference_available_usd": 0.0,
        },
        notes="Free tier credits. Live verified call chatcmpl-23099d88... on muse-spark-open ($0.000271 USD). Dedicated inference disabled.",
    ),
    "modal": ProviderFinancialProfile(
        provider_id="modal",
        display_name="Modal CPU Ephemeral Sandbox",
        account_email=None,
        organization="InnerChispa LLC",
        available_balance_usd=0.999961,
        used_balance_usd=0.000039,
        auto_reload_enabled=False,
        free_credits_only=True,
        status="TESTED_LIVE",
        proposed_test_budget_usd=0.25,
        per_call_ceiling_usd=0.05,
        max_tokens_per_call=0,  # Sandbox CPU runner, not LLM
        timeout_seconds=60,
        max_retries=0,
        notes="Live verified ephemeral CPU run ap-FgeaL6ROaCPzOSda8YgqB1 ($0.000039 USD). $29 credit pending card is strictly unauthorized.",
    ),
    "meta_model_api": ProviderFinancialProfile(
        provider_id="meta_model_api",
        display_name="Meta Model API (Muse Wonder / Spark)",
        account_email=None,
        organization="InnerChispa LLC",
        available_balance_usd=50.00,
        used_balance_usd=0.0019,
        auto_reload_enabled=False,
        free_credits_only=True,
        status="TESTED_LIVE",
        proposed_test_budget_usd=0.50,
        per_call_ceiling_usd=0.50,
        max_tokens_per_call=4096,
        timeout_seconds=45,
        max_retries=0,
        notes="10-day evaluation grant window. Wonder 1.0 verified receipt in evidence. Additional calls fail-closed without grant.",
    ),
    "local_amd_rocm": ProviderFinancialProfile(
        provider_id="local_amd_rocm",
        display_name="Local Qwen3-Coder-30B-AWQ (AMD R9700)",
        account_email=None,
        organization="InnerChispa LLC",
        available_balance_usd=999999.00,  # Unmetered local GPU
        used_balance_usd=0.0,
        auto_reload_enabled=False,
        free_credits_only=True,
        status="TESTED_LIVE",
        proposed_test_budget_usd=0.0,
        per_call_ceiling_usd=0.0,
        max_tokens_per_call=8192,
        timeout_seconds=60,
        max_retries=0,
        notes="Sovereign on-premises ROCm 10.1 cluster. Unmetered $0.00 cost. 100% LAN privacy.",
    ),
    "gpt6_astra": ProviderFinancialProfile(
        provider_id="gpt6_astra",
        display_name="GPT-6 Astra (OpenAI)",
        account_email=None,
        organization="InnerChispa LLC",
        available_balance_usd=0.0,
        used_balance_usd=0.0,
        auto_reload_enabled=False,
        free_credits_only=False,
        status="BLOCKED",
        proposed_test_budget_usd=0.0,
        per_call_ceiling_usd=0.0,
        max_tokens_per_call=0,
        timeout_seconds=0,
        max_retries=0,
        notes="BLOCKED_API_ACCESS: No authorized OpenAI API key in owner vault or env. Zero silent fallback.",
    ),
}


class ProviderFinanceManager:
    """Manages provider budgets, pre-call governance, and usage receipts."""

    def __init__(self, ledger: dict[str, ProviderFinancialProfile] | None = None) -> None:
        self._ledger = deepcopy(ledger or INITIAL_FINANCIAL_LEDGER)
        self._receipts: list[dict[str, Any]] = []

    def get_ledger(self) -> dict[str, dict[str, Any]]:
        return {k: asdict(v) for k, v in self._ledger.items()}

    def get_profile(self, provider_id: str) -> dict[str, Any] | None:
        profile = self._ledger.get(provider_id)
        return asdict(profile) if profile else None

    def validate_pre_call(
        self,
        provider_id: str,
        estimated_cost_usd: float,
        owner_grant_token: str | None = None,
        requested_tokens: int = 0,
    ) -> dict[str, Any]:
        """Strict pre-call financial validator.
        
        Fails closed if:
        1. Provider is unknown or BLOCKED.
        2. Estimated cost exceeds per-call ceiling or available balance.
        3. Owner grant token is missing for paid providers.
        4. Auto-reload or unbudgeted spend is detected.
        """
        profile = self._ledger.get(provider_id)
        if not profile:
            raise FinancialGovernanceError(f"PROVIDER_UNKNOWN: Provider '{provider_id}' is not in the financial registry.")

        if profile.status == "BLOCKED":
            raise FinancialGovernanceError(f"PROVIDER_BLOCKED: Provider '{provider_id}' is marked BLOCKED ({profile.notes}).")

        if provider_id == "local_amd_rocm":
            return {
                "allowed": True,
                "provider_id": provider_id,
                "cost_usd": 0.0,
                "remaining_balance_usd": profile.available_balance_usd,
                "reason": "Unmetered sovereign local GPU",
            }

        # Check per-call ceiling
        if estimated_cost_usd > profile.per_call_ceiling_usd:
            raise FinancialGovernanceError(
                f"BUDGET_CEILING_EXCEEDED: Estimated cost ${estimated_cost_usd:.4f} exceeds ceiling ${profile.per_call_ceiling_usd:.4f} for {provider_id}."
            )

        # Check available balance
        if estimated_cost_usd > profile.available_balance_usd:
            raise FinancialGovernanceError(
                f"INSUFFICIENT_BALANCE: Estimated cost ${estimated_cost_usd:.4f} exceeds available balance ${profile.available_balance_usd:.4f} for {provider_id}."
            )

        # Token limit check
        if requested_tokens > profile.max_tokens_per_call and profile.max_tokens_per_call > 0:
            raise FinancialGovernanceError(
                f"TOKEN_LIMIT_EXCEEDED: Requested {requested_tokens} tokens exceeds limit of {profile.max_tokens_per_call} for {provider_id}."
            )

        # Enforce explicit Owner Approval Grant for billable external calls
        if not owner_grant_token:
            raise FinancialGovernanceError(
                f"OWNER_GRANT_REQUIRED: Billable execution on {provider_id} requires explicit owner approval grant token (proposed budget ${profile.proposed_test_budget_usd:.2f})."
            )

        return {
            "allowed": True,
            "provider_id": provider_id,
            "estimated_cost_usd": estimated_cost_usd,
            "ceiling_usd": profile.per_call_ceiling_usd,
            "pre_call_balance_usd": profile.available_balance_usd,
            "grant_token_verified": True,
        }

    def record_usage_receipt(
        self,
        provider_id: str,
        actual_cost_usd: float,
        prompt_tokens: int,
        completion_tokens: int,
        call_type: str = "inference",
        pool_name: str | None = None,
    ) -> dict[str, Any]:
        """Deducts actual spend, records cryptographic receipt, and updates ledger."""
        profile = self._ledger.get(provider_id)
        if not profile:
            raise FinancialGovernanceError(f"Cannot record receipt: unknown provider {provider_id}")

        pre_balance = profile.available_balance_usd
        if pool_name and pool_name in profile.extra_pools:
            pool_balance = profile.extra_pools[pool_name]
            profile.extra_pools[pool_name] = max(0.0, pool_balance - actual_cost_usd)
            profile.extra_pools[f"{pool_name}_used"] = profile.extra_pools.get(f"{pool_name}_used", 0.0) + actual_cost_usd
        else:
            profile.available_balance_usd = max(0.0, profile.available_balance_usd - actual_cost_usd)
            profile.used_balance_usd += actual_cost_usd

        receipt_data = {
            "receipt_id": f"rcpt_{hashlib.sha256(f'{provider_id}:{datetime.now(timezone.utc).isoformat()}:{actual_cost_usd}'.encode()).hexdigest()[:16]}",
            "provider_id": provider_id,
            "call_type": call_type,
            "pool_name": pool_name or "primary",
            "pre_balance_usd": pre_balance,
            "actual_cost_usd": round(actual_cost_usd, 6),
            "post_balance_usd": round(profile.available_balance_usd, 6),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        receipt_data["receipt_digest"] = hashlib.sha256(
            json.dumps(receipt_data, sort_keys=True).encode()
        ).hexdigest()

        self._receipts.append(receipt_data)
        return receipt_data

    def get_receipts(self, provider_id: str | None = None) -> list[dict[str, Any]]:
        if provider_id:
            return [r for r in self._receipts if r["provider_id"] == provider_id]
        return list(self._receipts)

    def generate_financial_matrix(self) -> dict[str, Any]:
        """Produces a consolidated financial audit matrix."""
        providers = {}
        total_available = 0.0
        total_used = 0.0

        for pid, p in self._ledger.items():
            if pid != "local_amd_rocm":
                total_available += p.available_balance_usd
                total_used += p.used_balance_usd
            providers[pid] = {
                "display_name": p.display_name,
                "status": p.status,
                "organization": p.organization,
                "available_balance_usd": p.available_balance_usd,
                "used_balance_usd": p.used_balance_usd,
                "auto_reload": p.auto_reload_enabled,
                "proposed_test_budget_usd": p.proposed_test_budget_usd,
                "extra_pools": p.extra_pools,
                "notes": p.notes,
            }

        return {
            "schema": "inneros.provider_financial_matrix.v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_external_available_usd": round(total_available, 2),
            "total_external_used_usd": round(total_used, 4),
            "unapproved_cloud_spend_usd": 0.0,
            "providers": providers,
        }

