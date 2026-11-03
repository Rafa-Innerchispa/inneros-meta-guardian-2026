"""Evidence-led Muse Wonder case and safe stateful self-healing laboratory.

No model inference, network access, system commands, git writes, credentials,
or production task mutations occur in this module. Historical measurements are
labeled with their source and provenance level. The replay is IN_MEMORY_ONLY.
"""
from __future__ import annotations

import hashlib
import json
import threading
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

CORE_REPO = "https://github.com/Rafa-Innerchispa/innerops-agentic-platform"
DEMO_REPO = "https://github.com/Rafa-Innerchispa/inneros-meta-guardian-2026"
BEFORE_CI = CORE_REPO + "/actions/runs/41558176002"
AFTER_CI = CORE_REPO + "/actions/runs/41569825744"
WONDER_REPORT = DEMO_REPO + "/blob/main/docs/evidence/MUSE_WONDER_SELF_HEALING_VERIFIED_20261102.md"
WONDER_RECEIPT = DEMO_REPO + "/blob/main/docs/evidence/meta_wonder_receipt_20261102.json"
CORE_PR = CORE_REPO + "/pull/253"
AUTH_PR = CORE_REPO + "/pull/252"

CASES = [
    {
        "id": "F1", "name": "Local fallback error masked",
        "component": "local_model_router.py",
        "symptom": "Detailed local failure replaced by generic error.",
        "fix": "Preserve specific failure cause without cloud escalation.",
        "verification": "PR #253 CI passing; local-to-cloud escalation not enabled.",
        "truth": "SOURCE_CODE_AND_CI_VERIFIED",
    },
    {
        "id": "F2", "name": "Manual-only dispatch precedence",
        "component": "ops_auto_claim_admission.py",
        "symptom": "Global freeze masked the manual-only task reason.",
        "fix": "Check do_not_auto_dispatch before the freeze reason.",
        "verification": "PR #253 CI passing; automatic work admission unchanged.",
        "truth": "SOURCE_CODE_AND_CI_VERIFIED",
    },
    {
        "id": "F3", "name": "Headless worker completion contract",
        "component": "antigravity_ops_headless_execute_one.py",
        "symptom": "Regression fixture expected bounded plan but got rejection code 2.",
        "fix": "Fix test setup to carry claimed state and owner marker; keep production denials.",
        "verification": "CI passing with corrected fixture. No live worker repair claimed.",
        "truth": "TEST_CONTRACT_ADJUSTMENT",
    },
    {
        "id": "F4", "name": "External agent trust-boundary contract",
        "component": "interactive_provider_bounded_executor.py",
        "symptom": "Resource admission blocked before the mocked budget gate.",
        "fix": "Isolate resource guard in test; assert owner-budget grant fails closed.",
        "verification": "CI passing; real Meta/Codex spend path not invoked.",
        "truth": "TEST_CONTRACT_ADJUSTMENT",
    },
]

def case_evidence() -> dict[str, Any]:
    """A timestamped evidence snapshot. This is not a live MongoDB adapter."""
    return {
        "schema": "inneros.meta.judge_case.v1",
        "read_only": True,
        "snapshot_at": "2026-11-03T03:06:34Z",
        "truth": "HISTORICAL_SOURCE_BACKED_SNAPSHOT",
        "summary": {
            "name": "InnerOS agent-coordination self-healing",
            "hypothesis": "Local-first diagnosis + Meta reasoning can help restore safer coordination.",
            "method": "Review real CI, sanitize incident, compare model analysis, patch in disposable branch, independently test.",
            "claim": "Isolated code/test corrections, NOT autonomous production healing",
        },
        "live_coordination_snapshot": {
            "recorded_at": "2026-11-03T03:06:34Z",
            "revision": 48717,
            "open_records": 179,
            "blocked_records": 61,
            "stale_timeout_records": 41,
            "active_workers_reported": 0,
            "truth": "MCP_LEDGER_SNAPSHOT_NOT_LIVE_STREAM",
        },
        "original_ci": {
            "url": BEFORE_CI,
            "passed": 335,
            "failed": 4,
            "subtests_passed": 13,
            "truth": "GITHUB_ACTIONS_VERIFIED",
        },
        "candidate_ci": {
            "url": AFTER_CI,
            "passed": 339,
            "failed": 0,
            "subtests_passed": 13,
            "pr_url": CORE_PR,
            "truth": "GITHUB_ACTIONS_VERIFIED",
            "scope": "Branch PR #253; code/test changes, not live deployment",
        },
        "wonder": {
            "model": "muse-wonder-1.0",
            "provider": "Meta Model API",
            "response_id": "resp_6ae9322a12052fe018674cb6",
            "reported_http_status": 200,
            "reported_completion": "completed",
            "input_tokens": 312,
            "output_tokens": 3130,
            "reasoning_tokens_in_output": 1420,
            "total_tokens": 3442,
            "reported_latency_ms": 22059.672,
            "automatic_retries_reported": 0,
            "billing_verified_usd": None,
            "owner_approval_independently_verified": False,
            "truth": "OPERATOR_REPORTED_API_RECEIPT_UNRECONCILED",
            "receipt_url": WONDER_RECEIPT,
            "report_url": WONDER_REPORT,
            "note": "The model saw a sanitized fictional case, not live agents or private production logs.",
        },
        "release": {
            "auth_pr": AUTH_PR,
            "code_pr": CORE_PR,
            "production_merged": False,
            "production_verified_healed": False,
            "wonder_chat_mcp_wired": False,
            "public_paid_call_enabled": False,
        },
        "cases": deepcopy(CASES),
        "front_end_modes": {
            "physical": "Read-only live adapter where configured; virtual actuator",
            "coordination": "Historical evidence plus deterministic in-memory replay",
            "meta_live": "OPERATOR_ONLY_DISABLED_IN_WEB",
        },
    }


class LabError(ValueError):
    pass


class SelfHealingLab:
    """In-memory, non-production state machine to demonstrate the safety loop."""

    def __init__(self):
        self._lock = threading.RLock()
        self._sessions: dict[str, dict[str, Any]] = {}

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="milliseconds")

    @staticmethod
    def _digest(record: dict[str, Any]) -> str:
        raw = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _append(self, state: dict[str, Any], phase: str, payload: dict[str, Any]) -> None:
        prev = state["events"][-1]["hash"] if state["events"] else "0" * 64
        item = {
            "sequence": len(state["events"]) + 1, "phase": phase,
            "recorded_at": self._timestamp(), "previous_hash": prev,
            "payload": payload,
        }
        item["hash"] = self._digest(item)
        state["events"].append(item)

    def start(self, scenario: str = "stale_agent_claim") -> dict[str, Any]:
        if scenario != "stale_agent_claim":
            raise LabError("Unknown synthetic laboratory scenario")
        with self._lock:
            if len(self._sessions) >= 100:
                raise LabError("Sandbox session capacity reached; restart the local demo")
            sid = "lab_" + uuid.uuid4().hex[:20]
            state: dict[str, Any] = {
                "id": sid, "scenario": scenario, "status": "observed",
                "source_truth": "SIMULATED_REPLAY_NOT_LIVE_INNEROS",
                "fixture": {
                    "task_status": "claimed", "lease_expired": True,
                    "worker_running": False, "false_completed": False,
                },
                "diagnosis": None, "wonder": None, "approval": None,
                "patch": None, "verification": None, "events": [],
            }
            self._append(state, "OBSERVE", {
                "synthetic_problem": "Expired worker claim with no worker",
                "truth": "SIMULATED_FIXTURE",
            })
            self._sessions[sid] = state
            return self._public(state)

    def _lookup(self, sid: str) -> dict[str, Any]:
        state = self._sessions.get(sid)
        if not state:
            raise LabError("Unknown lab session")
        return state

    def _public(self, state: dict[str, Any]) -> dict[str, Any]:
        obj = deepcopy(state)
        obj["audit"] = self._verify_chain(state["events"])
        return obj

    def _verify_chain(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        prev = "0" * 64
        for index, event in enumerate(events, 1):
            row = {k: deepcopy(v) for k, v in event.items() if k != "hash"}
            if row["sequence"] != index or row["previous_hash"] != prev:
                return {"valid": False, "events": len(events), "failure_at": index}
            calc = self._digest(row)
            if calc != event.get("hash"):
                return {"valid": False, "events": len(events), "failure_at": index}
            prev = calc
        return {"valid": True, "events": len(events), "head_sha256": prev}

    def transition(self, sid: str, action: str, actor: str = "") -> dict[str, Any]:
        with self._lock:
            state = self._lookup(sid)
            expected = {
                "diagnose": "observed",
                "replay_wonder": "diagnosed",
                "acknowledge_lab": "reasoned",
                "apply_virtual_patch": "approved",
                "verify": "patched",
            }
            if action not in expected or state["status"] != expected[action]:
                raise LabError("Invalid laboratory transition; no state changed")
            if action == "diagnose":
                state["diagnosis"] = {
                    "method": "DETERMINISTIC_LOCAL_DIAGNOSTIC_NOT_QWEN",
                    "suspected_cause": "Lease expired; task still marked claimed",
                    "confidence": "rule_based",
                    "possible_action": "quarantine stale claim in isolated state",
                    "external_call": False,
                }
                state["status"] = "diagnosed"
                self._append(state, "LOCAL_DIAGNOSE", {"truth": "DETERMINISTIC_FIXTURE_REPLAY"})
            elif action == "replay_wonder":
                state["wonder"] = {
                    "mode": "HISTORICAL_RECEIPT_REFERENCE_ONLY",
                    "response_id": case_evidence()["wonder"]["response_id"],
                    "truth": "OPERATOR_REPORTED_NO_NEW_META_CALL",
                    "recommendation": "Patch smallest failure; verify separate runtime contracts.",
                }
                state["status"] = "reasoned"
                self._append(state, "REASON", {
                    "provider": "historical_muse_wonder_reference",
                    "actual_network_requests": 0,
                })
            elif action == "acknowledge_lab":
                if not 2 <= len(actor.strip()) <= 60:
                    raise LabError("Lab operator display name must be 2–60 characters")
                state["approval"] = {
                    "actor_display": actor.strip(), "truth": "LAB_ONLY_ACK_NOT_SIGNED_OWNER_GRANT",
                    "device_authorized": False, "paid_inference_authorized": False,
                }
                state["status"] = "approved"
                self._append(state, "LAB_ACK", {"truth": "UNAUTHENTICATED_SANDBOX_ACK"})
            elif action == "apply_virtual_patch":
                state["fixture"]["task_status"] = "blocked_for_review"
                state["patch"] = {
                    "description": "Quarantined stale claim in process memory only",
                    "truth": "IN_MEMORY_VIRTUAL_PATCH",
                    "git_commit": None, "production_files_changed": 0,
                }
                state["status"] = "patched"
                self._append(state, "VIRTUAL_ACT", {"production_mutations": 0})
            elif action == "verify":
                f = state["fixture"]
                passed = bool(
                    f["task_status"] == "blocked_for_review"
                    and f["lease_expired"] and not f["worker_running"]
                    and not f["false_completed"]
                )
                state["verification"] = {
                    "passed": passed,
                    "method": "independent fixture invariant readback",
                    "truth": "SANDBOX_VERIFICATION_NOT_PRODUCTION",
                }
                state["status"] = "verified" if passed else "failed_safe"
                self._append(state, "VERIFY", {
                    "passed": passed, "production_mutations": 0,
                })
            return self._public(state)

    def evidence(self, sid: str) -> dict[str, Any]:
        with self._lock:
            state = self._lookup(sid)
            return {
                "schema": "inneros.selfheal.sandbox_evidence.v1",
                "truth": "SIMULATED_REPLAY_NOT_LIVE_INNEROS",
                "lab": self._public(state),
                "independent_ci": {
                    "before": BEFORE_CI, "after": AFTER_CI,
                    "truth": "HISTORICAL_EXTERNAL_GITHUB_CI",
                },
                "meta_reference": {
                    "url": WONDER_RECEIPT,
                    "truth": "OPERATOR_REPORTED_NOT_REINVOKED",
                },
                "limitations": [
                    "No production agent was restarted, released or repaired.",
                    "No local Qwen or Meta model inference was executed by this lab.",
                    "Hash chain is local in-memory integrity, not external notarization.",
                    "Lab acknowledgement is not authenticated owner approval.",
                ],
            }
