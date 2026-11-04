"""HTTP integration for the self-healing judge console: no external services."""
from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from inneros_meta_guardian.context_collector import SNAPSHOT_SCHEMA
from inneros_meta_guardian.diagnostic_orchestrator import DiagnosticOrchestrator
from inneros_meta_guardian.engine import Guardian
from inneros_meta_guardian.selfheal_lab import SelfHealingLab
from inneros_meta_guardian.web import Handler


class SelfHealingWebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.guardian = Guardian(str(Path(cls.directory.name) / "selfheal_http.sqlite"))
        class TestHandler(Handler):
            pass
        TestHandler.guardian = cls.guardian
        TestHandler.selfheal_lab = SelfHealingLab()
        TestHandler.orchestrator = DiagnosticOrchestrator()
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), TestHandler)
        cls.root = "http://127.0.0.1:" + str(cls.server.server_port)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.guardian.close()
        cls.directory.cleanup()

    def get(self, path):
        with urllib.request.urlopen(self.root + path, timeout=5) as response:
            body = response.read().decode("utf-8")
            return response.status, body, response.headers.get("Content-Type", "")

    def post(self, path, body):
        req = urllib.request.Request(
            self.root + path,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))

    def test_judge_console_and_static_files_have_truth_labels(self):
        for route in ("/self-heal", "/self-heal.html"):
            status, html, mime = self.get(route)
            self.assertEqual(200, status)
            self.assertIn("text/html", mime)
            self.assertIn("Interactive self-healing replay", html)
            self.assertIn("5-Panel Muse &amp; Qwen Investigation Console", html)
            self.assertIn("SAFE REPLAY", html)
            self.assertIn("never calls the Meta API", html)
            self.assertIn("not a production release", html)
        status, script, mime = self.get("/self-heal.js")
        self.assertEqual(200, status)
        self.assertIn("javascript", mime)
        self.assertIn("No Meta request sent", script)
        self.assertNotIn("/api/grants", script)
        status, css, mime = self.get("/self-heal.css")
        self.assertEqual(200, status)
        self.assertIn("text/css", mime)
        self.assertIn(".lab-layout", css)
        self.assertIn(".console-5grid", css)

    def test_evidence_snapshot_route_does_not_claim_wonder_connected(self):
        code, raw, mime = self.get("/api/selfheal/case")
        self.assertEqual(200, code)
        self.assertIn("application/json", mime)
        data = json.loads(raw)
        self.assertEqual("HISTORICAL_SOURCE_BACKED_SNAPSHOT", data["truth"])
        self.assertFalse(data["release"]["wonder_chat_mcp_wired"])
        self.assertFalse(data["release"]["production_verified_healed"])
        self.assertFalse(data["wonder"]["owner_approval_independently_verified"])

    def test_orchestrator_snapshot_and_investigation_routes(self):
        code, raw, mime = self.get("/api/orchestrator/snapshot")
        self.assertEqual(200, code)
        self.assertIn("application/json", mime)
        snap = json.loads(raw)
        self.assertEqual(SNAPSHOT_SCHEMA, snap["schema"])
        self.assertEqual(64, len(snap["snapshot_sha256"]))

        code, session = self.post("/api/orchestrator/investigate", {
            "prompt": "Analiza por qué existen tareas pendientes sin ejecutarse.",
            "engine_mode": "hybrid_comparison",
        })
        self.assertEqual(201, code)
        self.assertEqual("COMPLETED_VERIFIED", session["status"])
        self.assertGreaterEqual(len(session["tool_history"]), 3)
        sid = session["session_id"]

        code, fetched_raw, _ = self.get("/api/orchestrator/sessions/" + sid)
        self.assertEqual(200, code)
        fetched = json.loads(fetched_raw)
        self.assertEqual(sid, fetched["session_id"])

        code, cancelled = self.post("/api/orchestrator/sessions/" + sid + "/cancel", {})
        self.assertEqual(200, code)
        self.assertEqual("CANCELLED", cancelled["status"])

    def test_sandbox_lifecycle_enforces_order_and_exports_proof(self):
        code, state = self.post("/api/selfheal/labs", {"scenario": "stale_agent_claim"})
        self.assertEqual(201, code)
        self.assertEqual("observed", state["status"])
        sid = state["id"]
        base = "/api/selfheal/labs/" + sid
        code, denied = self.post(base + "/transition", {"action": "apply_virtual_patch"})
        self.assertEqual(409, code)
        self.assertIn("Invalid laboratory transition", denied["error"])
        for action in ("diagnose", "replay_wonder", "acknowledge_lab", "apply_virtual_patch", "verify"):
            code, state = self.post(base + "/transition", {
                "action": action, "actor": "Demo operator",
            })
            self.assertEqual(200, code)
        self.assertEqual("verified", state["status"])
        self.assertEqual("SANDBOX_VERIFICATION_NOT_PRODUCTION", state["verification"]["truth"])
        self.assertTrue(state["audit"]["valid"])
        code, raw, _ = self.get(base + "/evidence")
        self.assertEqual(200, code)
        proof = json.loads(raw)
        self.assertEqual("SIMULATED_REPLAY_NOT_LIVE_INNEROS", proof["truth"])
        self.assertEqual(6, proof["lab"]["audit"]["events"])

    def test_meta_ecosystem_and_benchmark_routes(self):
        code, raw, mime = self.get("/api/meta/ecosystem")
        self.assertEqual(200, code)
        self.assertIn("application/json", mime)
        ecosystem = json.loads(raw)
        self.assertIn("components", ecosystem)
        self.assertGreaterEqual(len(ecosystem["components"]), 11)

        code, raw, mime = self.get("/api/meta/providers")
        self.assertEqual(200, code)
        providers = json.loads(raw)
        self.assertGreaterEqual(len(providers), 9)
        provider_ids = [p["id"] for p in providers]
        self.assertIn("muse-wonder-1.0", provider_ids)

        code, raw, mime = self.get("/api/meta/benchmark")
        self.assertEqual(200, code)
        benchmark = json.loads(raw)
        self.assertEqual("inneros.repair_benchmark_comparison.v1", benchmark["schema"])
        self.assertEqual("VERIFIED_PASS", benchmark["argon_repair"]["status"])
        self.assertEqual("BLOCKED_AWAITING_OWNER_AUTH", benchmark["muse_code_repair"]["auth_frontier_status"])

    def test_no_paid_web_execution_or_incorrect_real_scenario(self):
        code, data = self.post("/api/selfheal/labs", {"scenario": "real_server_reboot"})
        self.assertEqual(409, code)
        self.assertIn("Unknown synthetic", data["error"])
        code, data = self.post("/api/grants", {"snapshot_digest": "a" * 64})
        self.assertEqual(403, code)
        self.assertIn("META_OPERATOR_ONLY", data["error"])

if __name__ == "__main__":
    unittest.main()
