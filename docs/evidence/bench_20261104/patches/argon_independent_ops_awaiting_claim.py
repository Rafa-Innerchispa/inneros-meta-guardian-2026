"""Canonical awaiting_*_claim status for interactive IDE ops tasks."""

from __future__ import annotations

from typing import Any

from inneros_core_runtime.execution_binding import normalize_provider

_PROVIDER_AWAITING: dict[str, str] = {
    "cursor": "awaiting_cursor_claim",
    "codex": "awaiting_codex_claim",
    "antigravity": "awaiting_antigravity_claim",
    "gemini": "awaiting_gemini_claim",
}


def awaiting_claim_status_for_provider(provider: str) -> str:
    key = normalize_provider(provider)
    return _PROVIDER_AWAITING.get(key, "awaiting_ide_claim")


def _extract_lane_provider(lane: str | None) -> str:
    raw = str(lane or "").strip().lower()
    if not raw:
        return ""
    if raw.startswith("local_manual_"):
        raw = raw[len("local_manual_") :]
    if raw.endswith("_interactive"):
        raw = raw[: -len("_interactive")]
    return normalize_provider(raw)


def awaiting_claim_status_for_task(task: dict[str, Any] | None) -> str:
    if not task:
        return awaiting_claim_status_for_provider("cursor")

    direct_candidates = (
        task.get("assignee"),
        task.get("assigned_to"),
        task.get("preferred_provider"),
        task.get("claimed_by"),
        task.get("requested_agent"),
        _extract_lane_provider(task.get("execution_lane")),
        task.get("owner"),
    )
    for candidate in direct_candidates:
        if not candidate:
            continue
        key = normalize_provider(str(candidate))
        if key in _PROVIDER_AWAITING:
            return _PROVIDER_AWAITING[key]

    fallback = str(
        task.get("preferred_provider")
        or task.get("assignee")
        or task.get("assigned_to")
        or task.get("owner")
        or "cursor"
    ).strip()
    return awaiting_claim_status_for_provider(fallback)
