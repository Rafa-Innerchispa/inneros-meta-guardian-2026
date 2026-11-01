"""Integration tests for the HTTP server routes and API contracts."""
from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from inneros_meta_guardian.engine import Guardian
from inneros_meta_guardian.web import Handler


class WebRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        db_path = str(Path(cls.temp_dir.name) / "web_test.db")
        cls.guardian = Guardian(db_path)

        class TestServerHandler(Handler):
            pass

        TestServerHandler.guardian = cls.guardian
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), TestServerHandler)
        cls.port = cls.server.server_port
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.guardian.close()
        cls.temp_dir.cleanup()

    def _get(self, path: str) -> tuple[int, dict]:
        url = f"http://127.0.0.1:{self.port}{path}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return resp.status, data

    def _post(self, path: str, payload: dict) -> tuple[int, dict]:
        url = f"http://127.0.0.1:{self.port}{path}"
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data_bytes, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return resp.status, data
        except urllib.error.HTTPError as exc:
            data = json.loads(exc.read().decode("utf-8"))
            return exc.code, data

    def test_health_endpoint(self):
        status, data = self._get("/api/health")
        self.assertEqual(200, status)
        self.assertTrue(data["ok"])
        self.assertFalse(data["meta_supported"])

    def test_voiceops_receipt_endpoint(self):
        status, data = self._get("/api/voiceops/receipt")
        self.assertEqual(200, status)
        self.assertEqual("HISTORIC_RECORDED_VOICEOPS_CALL", data["truth"])
        self.assertEqual(7, data["speech_pipeline"]["accepted_stt_turns"])

    def test_sam_inspect_endpoint(self):
        status, data = self._get("/api/sam/inspect?asset=lab_rack_switch_led")
        self.assertEqual(200, status)
        self.assertEqual("SIMULATED_FIXTURE", data["status"])
        self.assertGreaterEqual(len(data["detected_objects"]), 2)

    def test_complete_web_incident_workflow(self):
        # 1. Ingest live reading
        with patch.object(self.guardian.live_client, "fetch_reading") as mock_fetch:
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
                "signals": [{"name": "wan_ping", "status": "up"}],
                "summary": {"signals_needing_review": 0},
                "snapshot_id": "snap_web_01",
                "snapshot_digest": "f" * 64,
                "limitations": [],
                "physical_mutation_applied": False,
            }
            status, inc = self._post("/api/incidents/live", {"site": "casa", "category": "network"})
        self.assertEqual(201, status)
        inc_id = inc["id"]

        # 2. Remember facts
        status, rem = self._post(f"/api/incidents/{inc_id}/remember", {"query": "topology"})
        self.assertEqual(200, status)
        self.assertIn("memory", rem)

        # 3. Anonymous HTTP cannot mint Meta grants.
        status, grant = self._post("/api/grants", {"snapshot_digest": inc["snapshot_digest"], "ttl_seconds": 120})
        self.assertEqual(403, status)
        self.assertIn("META_OPERATOR_ONLY", grant["error"])

        # 4. Anonymous HTTP cannot trigger paid Meta inference even with a token.
        status, denied = self._post(f"/api/incidents/{inc_id}/analyze", {"mode": "meta", "grant_token": "irrelevant"})
        self.assertEqual(403, status)
        self.assertIn("META_OPERATOR_ONLY", denied["error"])

        # Local deterministic analysis remains available for sandbox tests.
        status, analyzed = self._post(f"/api/incidents/{inc_id}/analyze", {"mode": "deterministic"})
        self.assertEqual(200, status)
        self.assertEqual("analyzed", analyzed["status"])

        # 5. Approve
        status, approved = self._post(
            f"/api/incidents/{inc_id}/approve",
            {"operator": "Rafael Lopez", "action": analyzed["recommended_action"]},
        )
        self.assertEqual(200, status)
        self.assertEqual("approved", approved["status"])

        # 6. Execute
        status, executed = self._post(f"/api/incidents/{inc_id}/execute", {})
        self.assertEqual(200, status)
        self.assertEqual("executed", executed["status"])

        # 7. Verify
        status, verified = self._post(f"/api/incidents/{inc_id}/verify", {})
        self.assertEqual(200, status)
        self.assertEqual("verified", verified["status"])

        # 8. Evidence
        status, evidence = self._get(f"/api/incidents/{inc_id}/evidence")
        self.assertEqual(200, status)
        self.assertTrue(evidence["global_chain_validation"]["valid"])


if __name__ == "__main__":
    unittest.main()
