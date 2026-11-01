"""End-to-End integration test covering the complete InnerOS Meta Guardian sequence:
OBSERVE -> REMEMBER -> REASON -> AUTHORIZE -> ACT -> VERIFY -> PROVE
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from inneros_meta_guardian.engine import Guardian
from inneros_meta_guardian.meta_once import GRANT_STORE


class EndToEndGovernanceTests(unittest.TestCase):
    def test_full_governed_lifecycle_with_live_observation_and_meta(self):
        with tempfile.TemporaryDirectory() as temp:
            db_path = str(Path(temp) / "e2e_test.db")
            guardian = Guardian(db_path)
            try:
                # 1. OBSERVE LIVE (mocked live reading)
                with patch.object(guardian.live_client, "fetch_reading") as mock_fetch:
                    mock_fetch.return_value = {
                        "ok": True,
                        "truth": "LIVE_INFRASTRUCTURE_READING",
                        "site": "casa",
                        "site_label": "CASA PRIMARY",
                        "category": "network",
                        "source": "guardian.creatorcore.ai",
                        "collected_at": "2026-11-01T12:00:00Z",
                        "source_observed_at": "2026-11-01T11:59:58Z",
                        "freshness": "fresh",
                        "signals": [
                            {"name": "core_switch_ping", "status": "up", "latency_ms": 1.2},
                            {"name": "aux_monitor_port", "status": "unreachable", "latency_ms": None},
                        ],
                        "summary": {"signal_count": 2, "signals_needing_review": 1},
                        "snapshot_id": "snap_test_e2e_01",
                        "snapshot_digest": "d" * 64,
                        "limitations": ["Auxiliary port unreachable requires FDB check"],
                        "physical_mutation_applied": False,
                    }
                    incident = guardian.ingest_live("casa", "network")

                self.assertEqual("LIVE_INFRASTRUCTURE_READING", incident["truth"])
                self.assertEqual("observed", incident["status"])
                self.assertEqual("d" * 64, incident["snapshot_digest"])

                # 2. REMEMBER (retrieve verified facts)
                rem = guardian.remember(incident["id"])
                self.assertIn("memory", rem)
                self.assertEqual("VERIFIED_HISTORICAL_MEMORY", rem["memory"]["truth"])
                self.assertGreater(len(rem["memory"]["facts"]), 0)

                # 3. REASON WITH META (One-shot grant issued and consumed)
                grant = GRANT_STORE.create_grant(incident["snapshot_digest"], ttl_seconds=300)
                analyzed = guardian.analyze(incident["id"], mode="meta", grant_token=grant["token"])
                self.assertEqual("analyzed", analyzed["status"])
                self.assertEqual("meta-muse-spark", analyzed["narration"]["provider"])
                self.assertIn("receipt", analyzed["narration"])

                # 4. AUTHORIZE (human approval required)
                approved = guardian.approve(
                    incident["id"],
                    operator="Rafael López (Owner)",
                    action=analyzed["recommended_action"],
                )
                self.assertEqual("approved", approved["status"])
                self.assertEqual("GOVERNED_HUMAN_APPROVAL", approved["approval"]["truth"])

                # 5. ACT (virtual actuator isolated)
                executed = guardian.execute(incident["id"])
                self.assertEqual("executed", executed["status"])
                self.assertEqual("GOVERNED_VIRTUAL_ACTUATION", executed["execution"]["truth"])

                # 6. VERIFY (readback + historical VoiceOps call receipt)
                verified = guardian.verify(incident["id"])
                self.assertEqual("verified", verified["status"])
                self.assertTrue(verified["verification"]["passed"])
                self.assertEqual("INDEPENDENT_READBACK_VERIFICATION", verified["verification"]["truth"])
                self.assertIn("voiceops_evidence", verified)
                self.assertEqual(
                    "HISTORIC_RECORDED_VOICEOPS_CALL",
                    verified["voiceops_evidence"]["truth"],
                )

                # 7. PROVE (tamper-evident SHA-256 hash chain validation)
                evidence_pack = guardian.evidence(incident["id"])
                self.assertTrue(evidence_pack["global_chain_validation"]["valid"])
                self.assertGreaterEqual(evidence_pack["global_chain_validation"]["entries"], 6)
            finally:
                guardian.close()


if __name__ == "__main__":
    unittest.main()
