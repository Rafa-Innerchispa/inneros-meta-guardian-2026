"""Security, privacy, and tamper-evident audit chain tests for InnerOS Meta Guardian."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from inneros_meta_guardian.engine import Guardian, LifecycleError
from inneros_meta_guardian.meta_once import GRANT_STORE, GrantError, MetaOnceOperator
from inneros_meta_guardian.sam_inspector import SAMInspector


class SecurityAndPrivacyTests(unittest.TestCase):
    def test_meta_payload_has_no_credentials_or_private_ips(self):
        digest = "e" * 64
        grant = GRANT_STORE.create_grant(digest)
        incident = {
            "site": "casa",
            "category": "network",
            "signals": [{"name": "wan", "gateway_ip": "192.168.1.1", "device_mac": "00:11:22:33:44:55"}],
            "snapshot_digest": digest,
            "secret_token": "supersecretpassword123",
        }
        memory = [{"title": "Credentials", "fact": "Internal secret token: admin123", "ip": "10.10.10.10"}]

        operator = MetaOnceOperator()
        with patch.object(operator, "api_key", "dummy_key"):
            with patch("urllib.request.urlopen") as mock_url:
                mock_url.return_value.__enter__.return_value.read.return_value = b'{"output": []}'
                try:
                    operator.execute_inference(grant["token"], incident, memory)
                except Exception:
                    pass

                # Inspect request sent to urllib
                self.assertEqual(1, mock_url.call_count)
                req = mock_url.call_args[0][0]
                sent_body = req.data.decode("utf-8")
                self.assertNotIn("192.168.1.1", sent_body)
                self.assertNotIn("00:11:22:33:44:55", sent_body)
                self.assertNotIn("supersecretpassword123", sent_body)
                self.assertIn("10.x.x.x", sent_body)

    def test_unapproved_incident_cannot_execute(self):
        guardian = Guardian()
        inc = guardian.ingest()
        with self.assertRaises(LifecycleError) as ctx:
            guardian.execute(inc["id"])
        self.assertIn("requires human approval", str(ctx.exception))
        guardian.close()

    def test_unanalyzed_incident_cannot_be_approved(self):
        guardian = Guardian()
        inc = guardian.ingest()
        with self.assertRaises(LifecycleError) as ctx:
            guardian.approve(inc["id"], "Operator", "notify_operator")
        self.assertIn("requires an analyzed incident", str(ctx.exception))
        guardian.close()

    def test_audit_hash_chain_detects_middle_entry_tampering(self):
        with tempfile.TemporaryDirectory() as temp:
            db_path = str(Path(temp) / "tamper_test.db")
            guardian = Guardian(db_path)
            try:
                inc = guardian.ingest()
                guardian.analyze(inc["id"])
                guardian.approve(inc["id"], "Operator", inc["recommended_action"])
                guardian.execute(inc["id"])
                guardian.verify(inc["id"])

                self.assertTrue(guardian.store.verify()["valid"])

                # Directly tamper with SQLite audit table
                guardian.store.db.execute("UPDATE audit SET payload=? WHERE seq=2", (json.dumps({"tampered": True}),))
                guardian.store.db.commit()

                # Verify should immediately fail
                verify_result = guardian.store.verify()
                self.assertFalse(verify_result["valid"])
                self.assertEqual(2, verify_result["broken_at"])
            finally:
                guardian.close()

    def test_sam_inspector_asset_isolation(self):
        inspector = SAMInspector()
        # Even with an arbitrary or path traversal attempt, fallback to lab asset
        result = inspector.inspect_lab_asset("../../etc/shadow")
        self.assertEqual("SIMULATED_FIXTURE", result["status"])
        self.assertEqual("lab_hw_01_core_switch", result["asset_id"])
        self.assertIn("no real image", result["privacy_compliance"])


if __name__ == "__main__":
    unittest.main()
