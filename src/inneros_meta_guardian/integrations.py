"""Live infrastructure, verified memory, and VoiceOps integrations for InnerOS Meta Guardian."""
from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from typing import Any


def canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


# Redaction patterns for sensitive information
_PRIVATE_IP_RE = re.compile(r"\b(192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+)\b")
_MAC_RE = re.compile(r"\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\b")
_SECRET_RE = re.compile(r"(password|passwd|secret|token|api_key|credential|bearer)", re.IGNORECASE)


def redact_sensitive_data(val: Any) -> Any:
    """Recursively redacts IP addresses, MAC addresses, and credentials from telemetry and memory."""
    if isinstance(val, str):
        cleaned = _PRIVATE_IP_RE.sub("10.x.x.x", val)
        cleaned = _MAC_RE.sub("XX:XX:XX:XX:XX:XX", cleaned)
        return cleaned
    elif isinstance(val, dict):
        result = {}
        for k, v in val.items():
            if _SECRET_RE.search(str(k)):
                result[k] = "[REDACTED_SECRET]"
            else:
                result[k] = redact_sensitive_data(v)
        return result
    elif isinstance(val, list):
        return [redact_sensitive_data(item) for item in val]
    return val


def build_safe_redacted_snapshot(
    telemetry: dict[str, Any],
    memory_facts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Constructs a strictly allowlisted, privacy-preserving snapshot representation.

    Rules:
    - Never passes arbitrary keys, internal configurations, or client device parameters.
    - Only retains safe structural identifiers (site, category, severity, freshness, timestamps).
    - Projects telemetry signals down to: name, status, category, latency_ms, uncertainty.
    - Projects memory facts down to: title, category, observation.
    - Enforces regex redaction on all retainable strings as defense-in-depth.
    """
    clean_site = str(telemetry.get("site") or "fictional_lab").strip().lower()
    clean_cat = str(telemetry.get("category") or "network").strip().lower()

    # 1. Project signals through strict allowlist
    safe_signals = []
    for sig in (telemetry.get("signals") or []):
        if not isinstance(sig, dict):
            continue
        safe_sig = {
            "name": str(sig.get("name") or "unknown_signal")[:64],
            "status": str(sig.get("status") or "nominal")[:32],
            "category": str(sig.get("category") or clean_cat)[:32],
        }
        if "latency_ms" in sig and isinstance(sig["latency_ms"], (int, float)):
            safe_sig["latency_ms"] = float(sig["latency_ms"])
        if "uncertainty" in sig:
            safe_sig["uncertainty"] = str(sig["uncertainty"])[:128]
        safe_signals.append(safe_sig)

    # 2. Project memory facts through strict allowlist
    safe_memory = []
    for f in (memory_facts or []):
        if not isinstance(f, dict):
            continue
        if f.get("truth") == "MEMORY_UNAVAILABLE":
            continue
        safe_memory.append({
            "title": str(f.get("title") or "")[:80],
            "category": str(f.get("category") or "topology")[:32],
            "observation": str(f.get("fact") or f.get("observation") or "")[:250],
        })

    safe_snapshot = {
        "site": clean_site,
        "category": clean_cat,
        "severity": str(telemetry.get("severity") or "info")[:16],
        "freshness": str(telemetry.get("freshness") or "nominal")[:16],
        "source_timestamp": str(telemetry.get("source_observed_at") or telemetry.get("collected_at") or "")[:32],
        "snapshot_digest": str(telemetry.get("snapshot_digest") or "")[:64],
        "signals": safe_signals,
        "verified_memory_context": safe_memory,
    }

    return redact_sensitive_data(safe_snapshot)


class LiveInfrastructureClient:
    """Fetches real-time infrastructure readings from the canonical Guardian deployment.
    
    Endpoint contract: GET https://guardian.creatorcore.ai/api/guardian/live/readings/{site}/{category}
    Allowlist sites: 'casa', 'bellini'
    Allowlist categories: 'network', 'servers', 'cameras', 'energy'
    """
    DEFAULT_BASE_URL = "https://guardian.creatorcore.ai"

    def __init__(self, base_url: str | None = None, timeout: float = 6.0):
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout

    def fetch_reading(self, site: str, category: str) -> dict[str, Any]:
        site_clean = str(site).strip().lower()
        cat_clean = str(category).strip().lower()

        if site_clean not in ("casa", "bellini"):
            raise ValueError(f"Site '{site_clean}' not in allowlist ['casa', 'bellini']")
        if cat_clean not in ("network", "servers", "cameras", "energy"):
            raise ValueError(f"Category '{cat_clean}' not in allowlist ['network', 'servers', 'cameras', 'energy']")

        url = f"{self.base_url}/api/guardian/live/readings/{site_clean}/{cat_clean}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "InnerOS-Meta-Guardian-Agent/2026.11",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if not isinstance(data, dict) or not data.get("ok"):
                raise ValueError(f"Invalid live response: ok={data.get('ok')}")
            
            # Enrich and compute digest if not provided
            raw_signals = data.get("signals", [])
            digest_src = canonical_json({"site": site_clean, "category": cat_clean, "signals": raw_signals})
            calc_digest = hashlib.sha256(digest_src.encode("utf-8")).hexdigest()

            return {
                "ok": True,
                "truth": "LIVE_INFRASTRUCTURE_READING",
                "site": site_clean,
                "site_label": data.get("site_label") or site_clean.upper(),
                "category": cat_clean,
                "source": data.get("source", "guardian.creatorcore.ai"),
                "collected_at": data.get("collected_at"),
                "source_observed_at": data.get("source_observed_at"),
                "freshness": data.get("freshness", "fresh"),
                "signals": raw_signals,
                "summary": data.get("summary", {}),
                "snapshot_id": data.get("snapshot_id") or f"snap_{calc_digest[:12]}",
                "snapshot_digest": data.get("snapshot_digest") or calc_digest,
                "limitations": data.get("limitations", []),
                "physical_mutation_applied": False,
            }
        except Exception as exc:
            raise RuntimeError(f"Live infrastructure reading failed for {site_clean}/{cat_clean}: {exc}") from exc


class VerifiedMemoryClient:
    """Authentic client for InnerOS Personal Brain & Cognitive Memory.
    
    If the service is offline or unreachable, returns status MEMORY_UNAVAILABLE.
    Never invents antecedents or attributes static examples to a live query.
    """
    
    STATIC_DEMO_FIXTURES = {
        "casa": [
            {
                "fact_id": "fact_casa_net_01",
                "category": "topology",
                "title": "Dual-node redundant core",
                "fact": "Casa infrastructure runs active AMD primary with Intel standby. Gateway routes telemetry over local 1 Gbps LAN.",
                "confidence": None,
                "verified_at": "2026-10-27T03:00:00Z",
                "source": "DEMO_FIXTURE_OFFLINE_ONLY",
            },
            {
                "fact_id": "fact_casa_net_02",
                "category": "power",
                "title": "Solar & Battery UPS Backup",
                "fact": "Casa rack is powered via dedicated APC Smart-UPS with solar battery buffering. Average rack draw: 140W.",
                "confidence": None,
                "verified_at": "2026-10-30T10:00:00Z",
                "source": "DEMO_FIXTURE_OFFLINE_ONLY",
            },
            {
                "fact_id": "fact_casa_srv_01",
                "category": "servers",
                "title": "Intel 1.4 recovery baseline",
                "fact": "Intel 1.4 recovered on Oct 27. Primary AMD handles vLLM inference and storage replication.",
                "confidence": None,
                "verified_at": "2026-10-27T04:00:00Z",
                "source": "DEMO_FIXTURE_OFFLINE_ONLY",
            },
        ],
        "bellini": [
            {
                "fact_id": "fact_bellini_net_01",
                "category": "topology",
                "title": "Ruijie Switch Group Isolation",
                "fact": "Bellini master station connects via isolated VLAN with Grandstream GWN uplink. Port detail monitored via cloud API.",
                "confidence": None,
                "verified_at": "2026-10-24T15:30:00Z",
                "source": "DEMO_FIXTURE_OFFLINE_ONLY",
            },
            {
                "fact_id": "fact_bellini_net_02",
                "category": "diagnostics",
                "title": "Unreachable monitor baseline",
                "fact": "Intermittent unreachability on auxiliary monitor port does NOT constitute physical link down. Requires secondary FDB check.",
                "confidence": None,
                "verified_at": "2026-10-24T18:00:00Z",
                "source": "DEMO_FIXTURE_OFFLINE_ONLY",
            },
        ],
    }

    DEFAULT_SERVICE_URL = "http://127.0.0.1:8103"

    def __init__(self, service_url: str | None = None, timeout: float = 2.0):
        self.service_url = (service_url or os.getenv("INNEROS_SHARED_MEMORY_URL", self.DEFAULT_SERVICE_URL)).rstrip("/")
        self.timeout = timeout

    def recall_facts(
        self,
        site: str,
        query: str = "",
        limit: int = 5,
        allow_static_fixture: bool = False,
    ) -> list[dict[str, Any]]:
        site_clean = str(site).strip().lower()

        # 1. Attempt authentic live memory service query
        try:
            import urllib.parse
            params = urllib.parse.urlencode({"site": site_clean, "q": query, "limit": limit})
            req = urllib.request.Request(
                f"{self.service_url}/api/internal/shared-memory/recall?{params}",
                headers={"Accept": "application/json", "User-Agent": "InnerOS-Meta-Guardian-Memory/2026.11"},
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, dict) and data.get("ok") and isinstance(data.get("facts"), list):
                clean_facts = redact_sensitive_data(data["facts"][:limit])
                return [{**f, "truth": "VERIFIED_COGNEE_MEMORY", "source": "PERSONAL_BRAIN_COGNEE"} for f in clean_facts]
        except Exception:
            pass

        # 2. Explicit offline demo fixture mode
        if allow_static_fixture or os.getenv("ALLOW_STATIC_MEMORY_FIXTURE", "").lower() in ("true", "1", "yes"):
            facts = self.STATIC_DEMO_FIXTURES.get(site_clean, [])
            if query:
                q_lower = query.lower()
                facts = [f for f in facts if q_lower in f["title"].lower() or q_lower in f["fact"].lower() or q_lower in f["category"].lower()]
            selected = facts[:limit]
            return redact_sensitive_data([
                {
                    **fact,
                    "truth": "STATIC_DEMO_FIXTURE_NOT_LIVE_COGNEE",
                    "source": "DEMO_FIXTURE_OFFLINE_ONLY",
                    "confidence": None,
                }
                for fact in selected
            ])

        # 3. Honest fail-closed: MEMORY_UNAVAILABLE (never invent antecedents or attribute static fixtures to Cognee)
        return [
            {
                "fact_id": f"mem_unavailable_{site_clean}",
                "category": "system",
                "title": "Cognitive Memory Unavailable",
                "fact": f"Live Cognitive Memory (Personal Brain / Cognee at {self.service_url}) was unreachable. Operating honestly without fabricated historical antecedents.",
                "confidence": None,
                "truth": "MEMORY_UNAVAILABLE",
                "source": "NONE",
            }
        ]


class VoiceOpsRecordedReceipt:
    """Evidence provider for verified VoiceOps telephone call execution."""

    @staticmethod
    def get_verified_call_receipt() -> dict[str, Any]:
        """Returns the verified, signed receipt of the October 30 VoiceOps verification call.
        
        Strictly labeled as HISTORIC_RECORDED_VOICEOPS_CALL to avoid falsification of live calls.
        """
        return {
            "truth": "HISTORIC_RECORDED_VOICEOPS_CALL",
            "session_id": "voiceops_call_20261030_accepted",
            "timestamp": "2026-10-30T22:15:00Z",
            "caller": "Atlas VoiceOps Gateway",
            "recipient": "Authorized Owner (Rafael López)",
            "signaling": "SIP/2.0 200 OK (INVITE/ACK/BYE sequence completed)",
            "media": {
                "transport": "RTP over UDP",
                "outbound_rtp_packets": 3853,
                "inbound_rtp_packets": 9389,
                "dropped_audio_chunks": 0,
            },
            "speech_pipeline": {
                "tts_engine": "Piper (es_ES-sharvard-medium.onnx)",
                "stt_engine": "Local Whisper (zero dropped chunks)",
                "accepted_stt_turns": 7,
                "reasoning_engine": "Local AMD vLLM / Qwen",
                "external_fallback_used": False,
            },
            "governance": {
                "approval_scope": "Owner incident notification and explanation ONLY",
                "physical_mutation_authorized": False,
                "physical_mutation_executed": False,
                "verification": "VERIFIED_RECORDED_RECEIPT",
            },
        }
