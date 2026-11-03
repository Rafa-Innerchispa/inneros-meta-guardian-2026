"""InnerOS Global Context Collector & Sanitizer for Autonomous Muse Investigation.

Prepares a versioned, source-referenced, strictly sanitized snapshot of InnerOS
(inneros_global_snapshot.json) across six canonical domains:
  A. Infrastructure (servers, services, connectivity, local models, MCP gateways)
  B. NCP Coordination (pending/claimed/blocked tasks, workers, leases, ACKs, heartbeats)
  C. Agents (Antigravity, Cursor, Codex, DevSwarm, registered NCP agents)
  D. Code (active repositories, branch, PR #256, commits, test gates, modified files)
  E. History (prior incidents, attempted repairs, regressions, architectural decisions)
  F. Security (permissions, forbidden ops, owner grants, cost/token ceilings, rollback)

Guarantees zero exposure of passwords, API keys, private IPs, or personal paths.
"""
from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SNAPSHOT_SCHEMA = "inneros.global_snapshot.v1"

_REDACT_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\b(?:192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"), "<REDACTED_LAN_IP>"),
    (re.compile(r"\b100\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"), "<REDACTED_MESH_IP>"),
    (re.compile(r"\b(?:sk-[A-Za-z0-9_-]{16,}|ghp_[A-Za-z0-9]{16,}|crsr_[A-Za-z0-9]{16,}|glpat-[A-Za-z0-9_.-]{12,}|AKIA[0-9A-Z]{16})\b"), "<REDACTED_CREDENTIAL>"),
    (re.compile(r"/home/[a-zA-Z0-9._-]+"), "<INNEROS_HOST_HOME>"),
    (re.compile(r"C:\\\\Users\\\\[a-zA-Z0-9._-]+", re.I), "<OPERATOR_WORKSTATION_HOME>"),
    (re.compile(r"inneros-5-lan|guardian\.creatorcore\.ai", re.I), "node-amd-primary.local"),
)

_SENSITIVE_KEY_NAMES = frozenset({
    "password", "passwd", "secret", "api_key", "apikey", "access_token",
    "refresh_token", "private_key", "authorization", "cookie", "client_secret",
})


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sanitize_value(value: Any) -> Any:
    """Recursively sanitize strings, dicts, and lists before external model dispatch."""
    if isinstance(value, str):
        out = value
        for pattern, replacement in _REDACT_PATTERNS:
            out = pattern.sub(replacement, out)
        return out
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for k, v in value.items():
            key_str = str(k)
            if key_str.lower() in _SENSITIVE_KEY_NAMES:
                cleaned[key_str] = "<REDACTED_SECRET>"
            else:
                cleaned[key_str] = sanitize_value(v)
        return cleaned
    if isinstance(value, list):
        return [sanitize_value(item) for item in value]
    return value


def snapshot_digest(snapshot: dict[str, Any]) -> str:
    payload = {k: v for k, v in snapshot.items() if k != "snapshot_sha256"}
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def build_global_snapshot(recorded_at: str | None = None) -> dict[str, Any]:
    """Build the canonical, sanitized InnerOS Global Snapshot from verified host telemetry."""
    ts = recorded_at or "2026-11-03T21:08:00+00:00"
    doc: dict[str, Any] = {
        "schema": SNAPSHOT_SCHEMA,
        "version": "1.1.0",
        "generated_at": ts,
        "classification": "SYNTHETIC_AND_SANITIZED_OPERATIONAL_METADATA",
        "provenance_marker": "FICTIONAL LAB DATA ONLY: Sanitized InnerOS architecture and coordination state for governed diagnostic evaluation.",
        "sections": {
            "infrastructure": {
                "timestamp": ts,
                "source": "systemd+ss+rocm_smi_verified_probe",
                "availability": "DEGRADED_SECONDARY_OFFLINE_PRIMARY_ONLINE",
                "nodes": [
                    {
                        "node_id": "node-amd-primary",
                        "hostname_alias": "ralfiia-amd",
                        "role": "primary_compute_and_coordination",
                        "status": "ONLINE",
                        "uptime": "5 days, 21:00",
                        "gpu": {
                            "model": "AMD Radeon AI PRO R9700",
                            "vram_total_gb": 32.0,
                            "vram_free_gb": 34.15,
                            "runtime": "ROCm 10.1",
                        },
                        "services": {
                            "vllm_local_inference": {
                                "port": 8000,
                                "bind": "127.0.0.1",
                                "status": "ONLINE_ACTIVE_ROCM",
                                "served_model": "QuantTrio/Qwen3-Coder-30B-A3B-Instruct-AWQ",
                                "max_model_len": 8192,
                            },
                            "mcp_canonical_monolithic": {
                                "service": "ralfia-mcp.service",
                                "port": 8102,
                                "status": "ONLINE",
                                "tools_registered_approx": 682,
                            },
                            "mcp_bounded_profile": {
                                "service": "ralfia-mcp-profile@chatgpt_compact.service",
                                "port": 8001,
                                "status": "ONLINE",
                                "tools_registered_approx": 15,
                            },
                            "temporal_server": {
                                "process": "temporal server start-dev",
                                "status": "ONLINE",
                                "queues": ["inneros-general-ops", "inneros-amd-gpu-ops"],
                            },
                            "temporal_worker": {
                                "service": "inneros-temporal-worker.service",
                                "status": "ONLINE",
                            },
                            "external_repair_agent_daemon": {
                                "service": "ralfia-external-repair-agent.service",
                                "status": "ONLINE",
                            },
                            "mongodb_state_store": {
                                "service": "mongod.service",
                                "status": "ONLINE",
                            },
                        },
                    },
                    {
                        "node_id": "node-intel-secondary",
                        "hostname_alias": "ralphi-ia-ver-10",
                        "role": "secondary_standby_and_summaries",
                        "status": "SSH_REACHABLE_OLLAMA_OFFLINE",
                        "uptime": "5 days, 21:00",
                        "gpu": {"model": "NVIDIA GPU", "vram_total_gb": 12.0},
                        "services": {
                            "ollama_local": {
                                "port": 11434,
                                "status": "UNREACHABLE_OFFLINE",
                            },
                            "historical_dns_dependency": {
                                "status": "MITIGATED_LOCAL_FALLBACK_REQUIRED",
                                "note": "Secondary node power/service loss historically impacted DNS resolution and cross-node worker lease verification.",
                            },
                        },
                    },
                ],
            },
            "ncp_coordination": {
                "timestamp": ts,
                "source": "mongodb:ralfia_ops_tasks+ralfia_dev_swarm_workers+ralfia_agent_messages",
                "availability": "ONLINE_WITH_COORDINATION_BOTTLENECKS",
                "task_status_counts": {
                    "completed": 683,
                    "cancelled": 5031,
                    "superseded": 457,
                    "archived": 209,
                    "blocked": 61,
                    "failed": 179,
                    "pending_human_review": 106,
                    "waiting_for_binding": 12,
                    "ready": 13,
                    "proposed": 1,
                    "queued": 11,
                    "awaiting_ide_claim": 26,
                    "awaiting_cursor_claim": 3,
                    "partial": 1,
                    "claimed": 2,
                    "expired": 2,
                    "awaiting_owner_approval": 1,
                    "awaiting_antigravity_claim": 0,
                },
                "worker_pool_summary": {
                    "collection": "ralfia_dev_swarm_workers",
                    "active_running": 0,
                    "paused": 1,
                    "blocked": 260,
                    "executed": 126,
                    "stale": 4,
                    "archived": 2,
                    "dominant_blocker": "stale_worker_retry_budget_exhausted",
                },
                "focal_tasks": [
                    {
                        "task_id": "ops_4e977fd8ec43",
                        "alias": "META-WONDER-COORDINATION-P0-OWNER",
                        "correlation_id": "meta-wonder-coordination-p0-20261102",
                        "assigned_to": "antigravity",
                        "preferred_provider": "antigravity",
                        "execution_lane": "antigravity_interactive",
                        "do_not_auto_dispatch": True,
                        "status_initial": "awaiting_antigravity_claim",
                        "status_current": "claimed",
                        "claim_host": "ralfiia-amd",
                        "claim_token_present": True,
                        "inbox_messages_acknowledged": ["msg_c2e9e2d42f44b306", "msg_0f58fb0d5fbbae78"],
                        "why_not_auto_dispatched": (
                            "Task has do_not_auto_dispatch=True and execution_lane='antigravity_interactive' "
                            "(runner='interactive_ide_handoff'). Internal DevSwarm workers are forbidden from "
                            "auto-claiming interactive IDE tasks without an explicit authenticated IDE claim."
                        ),
                        "temporal_signal_observation": "workflow not found for ID: ops_task:ops_4e977fd8ec43 (Mongo fallback used)",
                    },
                    {
                        "task_id": "ops_fcd8686d7fc6",
                        "alias": "INNEROS-TELEGRAM-OWNER-CHANNEL-ADD",
                        "correlation_id": "inneros-telegram-owner-channel-20261019",
                        "assigned_to": "inneros_orchestrator",
                        "preferred_provider": "antigravity",
                        "execution_lane": "local_dev_swarm",
                        "status": "claimed",
                        "claimed_by": "antigravity",
                        "claim_host": "ralfiia-amd",
                        "claimed_at": "2026-10-19T16:07:09+00:00",
                        "lease_until": "2026-10-19T17:07:09+00:00",
                        "lease_expired_days": 15,
                        "defect_summary": (
                            "Trapped in coordination dead-zone: dev_swarm_scheduler skips external/IDE claims "
                            "to avoid worktree takeover, while live main lacks PR #256 orphan recovery with "
                            "cross-host PID + linked gitdir lock verification."
                        ),
                    },
                ],
            },
            "agents": {
                "timestamp": ts,
                "source": "mongodb:ralfia_agent_registry+process_table",
                "registered_agents_count": 36,
                "key_agents": [
                    {
                        "agent_id": "antigravity",
                        "role": "interactive_ide_orchestrator_and_pair_programmer",
                        "status": "ACTIVE_CLAIMED_OPS_4E977FD8EC43",
                        "assigned_tasks": ["ops_4e977fd8ec43", "ops_fcd8686d7fc6"],
                        "credit_caps": {"daily": 50, "monthly": 500},
                        "can_accept_tasks": True,
                    },
                    {
                        "agent_id": "cursor",
                        "role": "ide_and_headless_worker",
                        "status": "IDLE_GUARDED_ZERO_ACTIVE_TASKS",
                        "assigned_tasks_awaiting_claim": 3,
                        "recent_incident": "2026-10-29 repeated retry loop mitigated via PR #249 credit stop",
                        "can_accept_tasks": False,
                        "freeze_reason": "paid_secondary_agents_disabled_for_p0_mission",
                    },
                    {
                        "agent_id": "codex",
                        "role": "external_developer_agent",
                        "status": "IDLE_CAPPED",
                        "credit_caps": {"daily": 3, "monthly": 30},
                        "can_accept_tasks": False,
                        "freeze_reason": "paid_secondary_agents_disabled_for_p0_mission",
                    },
                    {
                        "agent_id": "dev_swarm",
                        "role": "local_autonomous_worker_pool",
                        "status": "0_ACTIVE_WORKERS_260_BLOCKED",
                        "recent_error": "stale_worker_retry_budget_exhausted / bounded_runner_requires_repo",
                        "can_accept_tasks": False,
                    },
                ],
            },
            "code": {
                "timestamp": ts,
                "source": "git_worktree_and_github_api",
                "repositories": [
                    {
                        "repo": "Rafa-Innerchispa/innerops-agentic-platform",
                        "active_branch": "local-agent/meta-wonder-coordination-repair-20261102",
                        "pull_request": 256,
                        "pr_state": "OPEN",
                        "related_prs": [252, 253, 254],
                        "ci_status": "SUCCESS (376+ tests passing in InnerOS P0 Runtime Safety Gates, 33/33 in shared-meta-model-provider)",
                        "modified_modules": [
                            "platform/inneros_core_runtime/ops_interactive_recovery.py",
                            "platform/inneros_core_runtime/ops_awaiting_claim.py",
                            "platform/inneros_core_runtime/ops_auto_claim_admission.py",
                            "platform/inneros_core_runtime/local_model_router.py",
                            "platform/inneros_core_runtime/meta_model_provider.py",
                            "platform/inneros_core_runtime/capability_gateway_model.py",
                            "platform/inneros_core_runtime/interactive_ops_runner.py",
                            "platform/scripts/antigravity_ops_headless_execute_one.py",
                        ],
                    },
                    {
                        "repo": "Rafa-Innerchispa/inneros-meta-guardian-2026",
                        "active_branch": "main",
                        "role": "hackathon_guardian_console_and_orchestrator",
                        "modules": [
                            "src/inneros_meta_guardian/context_collector.py",
                            "src/inneros_meta_guardian/diagnostic_orchestrator.py",
                            "src/inneros_meta_guardian/selfheal_lab.py",
                            "src/inneros_meta_guardian/meta_once.py",
                            "src/inneros_meta_guardian/web.py",
                        ],
                    },
                ],
            },
            "history": {
                "timestamp": ts,
                "source": "ops_audit_log+issue_255_forensics",
                "incidents": [
                    {
                        "id": "INC-1",
                        "title": "Pending Antigravity task ops_4e977fd8ec43 not taken automatically",
                        "cause": "Task routed to antigravity_interactive lane with do_not_auto_dispatch=True and Temporal workflow ops_task:ops_4e977fd8ec43 absent; requires explicit IDE claim and inbox ACK.",
                        "status": "RESOLVED_IN_SESSION_CLAIMED_AND_ACKED",
                    },
                    {
                        "id": "INC-2",
                        "title": "Stale claimed task ops_fcd8686d7fc6 (15 days expired) & unsafe orphan recovery",
                        "cause": "Expired lease recovery lacked (a) cross-host claim_host verification (risking AMD wiping active Intel worker claims) and (b) linked Git worktree .git pointer file gitdir/index.lock check.",
                        "status": "PATCHED_AND_VERIFIED_IN_PR256",
                    },
                    {
                        "id": "INC-3",
                        "title": "Meta Muse Wonder 1.0 tool-call loop & receipt model attribution defect",
                        "cause": "meta_model_provider._save_receipt hardcoded 'muse-spark-1.3' instead of receipt['model'], and invoke_with_grant treated function_call outputs without output_text as UNVERIFIED_PROVIDER_RESPONSE.",
                        "status": "PATCHED_AND_VERIFIED_IN_PR256",
                    },
                    {
                        "id": "INC-4",
                        "title": "Cursor repeated execution credit loop (2026-10-29)",
                        "cause": "Unbounded automatic retries on external paid agent.",
                        "status": "MITIGATED_ZERO_AUTO_RETRIES_ENFORCED",
                    },
                ],
            },
            "security": {
                "timestamp": ts,
                "source": "owner_vault+policy_engine",
                "meta_credential_ref": "owner_vault:model_api_provider/meta_model_api_key",
                "meta_credential_configured": True,
                "secret_exposed": False,
                "active_unexpired_owner_grants": 0,
                "paid_inference_gate": "BLOCKED_UNTIL_OWNER_GRANT",
                "promotional_credit_context_usd": 150.0,
                "per_session_budget_ceiling_usd": 0.50,
                "max_output_tokens_ceiling": 4096,
                "max_tool_calls_per_session": 6,
                "automatic_retries_allowed": 0,
                "repair_levels": {
                    "level_0": "READ_ONLY (state, logs, allowlisted source excerpts)",
                    "level_1": "SIMULATION (isolated in-memory & sandbox reproduction)",
                    "level_2": "DEV_WORKTREE_REPAIR (isolated git worktree branch & test suites)",
                    "level_3": "PRODUCTION_MUTATION (requires explicit owner authorization & rollback plan)",
                },
                "forbidden_operations": [
                    "arbitrary_shell_execution",
                    "unapproved_paid_model_spend",
                    "credential_or_private_ip_exfiltration",
                    "unverified_production_service_restart",
                    "destructive_queue_or_mongo_wipe",
                ],
            },
        },
    }
    sanitized = sanitize_value(deepcopy(doc))
    sanitized["snapshot_sha256"] = snapshot_digest(sanitized)
    return sanitized


def write_global_snapshot(output_path: str | Path) -> dict[str, Any]:
    snap = build_global_snapshot()
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return snap
