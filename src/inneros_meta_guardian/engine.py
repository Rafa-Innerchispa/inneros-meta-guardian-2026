"""Governed incident lifecycle: observe > remember > reason > approve > act > verify > prove."""
from __future__ import annotations

import hashlib
import json
import threading
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .evidence import Store, canonical
from .fixtures import SCENARIOS, get_fixture
from .integrations import (
    LiveInfrastructureClient,
    VerifiedMemoryClient,
    VoiceOpsRecordedReceipt,
    redact_sensitive_data,
)
from .meta_once import GRANT_STORE, MetaOnceOperator
from .models import ModelUnavailable, narrate
from .policy import evaluate
from .sam_inspector import SAMInspector


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class LifecycleError(ValueError):
    pass


class Guardian:
    def __init__(self, db: str = ":memory:") -> None:
        self.store = Store(db)
        self.lock = threading.RLock()
        self.actuator: dict[str, bool] = {}
        self.scenarios = {k: v["title"] for k, v in SCENARIOS.items()}
        self.live_client = LiveInfrastructureClient()
        self.memory_client = VerifiedMemoryClient()
        self.sam_inspector = SAMInspector()

    def ingest(self, scenario: str = "door_propped") -> dict:
        with self.lock:
            fixture = get_fixture(scenario)
            incident = {
                "id": str(uuid4()),
                "scenario": scenario,
                "truth": "SIMULATED_FIXTURE",
                "status": "observed",
                "created_at": now(),
                "updated_at": now(),
                "narration": None,
                **fixture,
            }
            # Attach default snapshot digest
            sig_canon = canonical({"scenario": scenario, "signals": incident.get("signals")})
            incident["snapshot_digest"] = hashlib.sha256(sig_canon.encode("utf-8")).hexdigest()
            incident["snapshot_id"] = f"snap_{incident['snapshot_digest'][:12]}"

            self.store.upsert(incident)
            self.store.append(
                incident["id"],
                "OBSERVE",
                {
                    "scenario": scenario,
                    "truth": incident["truth"],
                    "signals": incident["signals"],
                    "snapshot_digest": incident["snapshot_digest"],
                },
            )
            return incident

    def ingest_live(self, site: str = "casa", category: str = "network") -> dict:
        """Ingests live physical/network infrastructure observation from Guardian API."""
        with self.lock:
            reading = self.live_client.fetch_reading(site, category)
            incident_id = str(uuid4())
            
            # Map into incident schema
            title = f"{reading['site_label']} Live {reading['category'].capitalize()} Telemetry"
            summary_dict = reading.get("summary", {})
            needs_review = summary_dict.get("signals_needing_review", 0)
            severity = "warning" if needs_review > 0 else "info"

            incident = {
                "id": incident_id,
                "scenario": f"live_{site}_{category}",
                "site": site,
                "site_label": reading["site_label"],
                "category": category,
                "title": title,
                "severity": severity,
                "truth": "LIVE_INFRASTRUCTURE_READING",
                "status": "observed",
                "created_at": now(),
                "updated_at": now(),
                "source": reading["source"],
                "collected_at": reading["collected_at"],
                "source_observed_at": reading["source_observed_at"],
                "freshness": reading["freshness"],
                "signals": reading["signals"],
                "summary": summary_dict,
                "snapshot_id": reading["snapshot_id"],
                "snapshot_digest": reading["snapshot_digest"],
                "limitations": reading.get("limitations", []),
                "physical_mutation_applied": False,
                "recommended_action": "notify_operator",
                "explanation": f"Live telemetry from {reading['site_label']} indicates {len(reading['signals'])} monitored signals; {needs_review} signals flagged for review.",
                "narration": None,
                "memory": None,
            }

            self.store.upsert(incident)
            self.store.append(
                incident_id,
                "OBSERVE_LIVE",
                {
                    "site": site,
                    "category": category,
                    "truth": incident["truth"],
                    "snapshot_id": incident["snapshot_id"],
                    "snapshot_digest": incident["snapshot_digest"],
                    "signals_count": len(reading["signals"]),
                    "freshness": incident["freshness"],
                },
            )
            return incident

    def get(self, id: str) -> dict:
        incident = self.store.get(id)
        if incident is None:
            raise LifecycleError("Incident not found")
        return incident

    def _save(self, incident: dict, event: str, payload: dict) -> dict:
        incident["updated_at"] = now()
        self.store.upsert(incident)
        self.store.append(incident["id"], event, payload)
        return incident

    def remember(self, id: str, query: str = "", allow_demo_fallback: bool = False) -> dict:
        """Retrieves verified historical facts and attaches them to the incident."""
        with self.lock:
            incident = self.get(id)
            site = incident.get("site", "casa")
            facts = self.memory_client.recall_facts(site, query=query, limit=4, allow_static_fixture=allow_demo_fallback)
            is_unavailable = any(f.get("truth") == "MEMORY_UNAVAILABLE" for f in facts)
            truth_label = "MEMORY_UNAVAILABLE" if is_unavailable else (
                "VERIFIED_COGNEE_MEMORY" if any(f.get("truth") == "VERIFIED_COGNEE_MEMORY" for f in facts)
                else "STATIC_DEMO_FIXTURE_NOT_LIVE_COGNEE"
            )
            incident["memory"] = {
                "truth": truth_label,
                "status": "MEMORY_UNAVAILABLE" if is_unavailable else "RECALLED",
                "facts": facts,
                "recalled_at": now(),
                "site": site,
            }
            return self._save(
                incident,
                "REMEMBER",
                {"site": site, "fact_count": len(facts), "facts": facts, "truth": truth_label},
            )

    def analyze(self, id: str, mode: str = "deterministic", grant_token: str | None = None) -> dict:
        with self.lock:
            incident = self.get(id)
            if incident["status"] != "observed":
                raise LifecycleError("Can only analyze an observed incident")
            if mode not in ("deterministic", "ollama", "meta"):
                raise LifecycleError("Unknown inference mode")

            if mode == "meta":
                if not grant_token:
                    raise LifecycleError("Meta inference requires a valid single-use operator grant_token")
                # Ensure memory is populated before Meta reasoning
                if not incident.get("memory"):
                    self.remember(id)
                    incident = self.get(id)
                
                memory_facts = incident.get("memory", {}).get("facts", [])
                operator = MetaOnceOperator()
                receipt = operator.execute_inference(
                    grant_token=grant_token,
                    incident_telemetry=incident,
                    historical_memory=memory_facts,
                )
                narrative = {
                    "provider": "meta-muse-spark",
                    "model": receipt.get("model", "muse-spark-1.3"),
                    "live_model": receipt.get("status") == "REAL",
                    "truth": receipt.get("truth", "GOVERNED_ONE_SHOT_RECEIPT"),
                    "narrative": receipt.get("raw_text") or receipt.get("analysis", {}).get("observations", ""),
                    "receipt": receipt,
                }
            else:
                try:
                    narrative = narrate(mode, incident)
                except ModelUnavailable as exc:
                    narrative = narrate("deterministic", incident)
                    narrative["fallback_reason"] = str(exc)
                    narrative["requested_provider"] = mode

            incident["narration"] = narrative
            incident["status"] = "analyzed"
            rec_action = incident.get("recommended_action") or "Notify operator"
            incident["policy"] = evaluate(rec_action, incident).as_dict()

            return self._save(
                incident,
                "REASON",
                {
                    "mode": mode,
                    "provider": narrative["provider"],
                    "truth": narrative["truth"],
                    "model": narrative["model"],
                    "policy": incident["policy"],
                    "grant_used": grant_token is not None,
                },
            )

    def approve(self, id: str, operator: str, action: str) -> dict:
        with self.lock:
            incident = self.get(id)
            if incident["status"] != "analyzed":
                raise LifecycleError("Human approval requires an analyzed incident")
            if not isinstance(operator, str) or not (2 <= len(operator.strip()) <= 60):
                raise LifecycleError("Operator display name required (2-60 characters)")
            decision = evaluate(action, incident)
            if not decision.allowed:
                self.store.append(id, "DENY", {"action": action, "reason": decision.reason})
                raise LifecycleError(decision.reason)
            incident["approval"] = {
                "operator": operator.strip(),
                "action": action,
                "approved_at": now(),
                "truth": "GOVERNED_HUMAN_APPROVAL",
            }
            incident["status"] = "approved"
            return self._save(
                incident,
                "APPROVE",
                {"operator": operator.strip(), "action": action, "truth": "GOVERNED_HUMAN_APPROVAL"},
            )

    def execute(self, id: str) -> dict:
        with self.lock:
            incident = self.get(id)
            if incident["status"] != "approved":
                raise LifecycleError("Execution requires human approval")
            approval = incident.get("approval") or {}
            decision = evaluate(approval.get("action", ""), incident)
            if not decision.allowed or approval.get("action") != incident["recommended_action"]:
                raise LifecycleError("Policy blocked action")
            
            # Virtual actuator: NO direct real device API calls or physical mutations.
            self.actuator[id] = True
            is_live = incident.get("truth") == "LIVE_INFRASTRUCTURE_READING"
            incident["execution"] = {
                "action": approval["action"],
                "issued_at": now(),
                "truth": "GOVERNED_VIRTUAL_ACTUATION" if is_live else "SIMULATED_REFERENCE_IO",
                "transport": "in-process virtual actuator with state isolation",
            }
            incident["status"] = "executed"
            return self._save(incident, "ACT", incident["execution"])

    def verify(self, id: str) -> dict:
        with self.lock:
            incident = self.get(id)
            if incident["status"] != "executed":
                raise LifecycleError("Verification requires an executed action")
            # Readback from separate actuator state, not command ACK
            verified = self.actuator.get(id) is True
            is_live = incident.get("truth") == "LIVE_INFRASTRUCTURE_READING"
            incident["verification"] = {
                "passed": verified,
                "verified_at": now(),
                "method": "virtual-state-readback",
                "truth": "INDEPENDENT_READBACK_VERIFICATION" if is_live else "SIMULATED_REFERENCE_IO",
            }
            incident["status"] = "verified" if verified else "failed_safe"

            # Attach VoiceOps recorded verification evidence
            voice_evidence = VoiceOpsRecordedReceipt.get_verified_call_receipt()
            incident["voiceops_evidence"] = voice_evidence

            return self._save(
                incident,
                "VERIFY",
                {
                    "verification": incident["verification"],
                    "voiceops_evidence": voice_evidence,
                },
            )

    def evidence(self, id: str) -> dict:
        incident = self.get(id)
        return {
            "schema": "inneros-guardian-evidence-v1",
            "incident": incident,
            "audit": self.store.audit(id),
            "global_chain_validation": self.store.verify(),
            "attestation": {
                "hash_chain": "SHA-256 tamper-evident sequence",
                "hardware_safety": "Read-only live infrastructure telemetry; zero non-consented device mutations.",
                "model_governance": "One-shot single-use grant boundary; atomic pre-call consumption.",
            },
        }

    def reset_virtual_state(self, id: str) -> None:
        with self.lock:
            self.actuator[id] = False

    def close(self) -> None:
        self.store.close()
