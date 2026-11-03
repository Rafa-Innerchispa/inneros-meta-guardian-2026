"""Safety and provenance regressions for the InnerOS judge self-healing lab."""
from __future__ import annotations

import json
import threading
import unittest
from unittest.mock import patch

from inneros_meta_guardian.context_collector import (
    SNAPSHOT_SCHEMA, build_global_snapshot, sanitize_value,
)
from inneros_meta_guardian.diagnostic_orchestrator import (
    TOOL_SCHEMAS, DiagnosticOrchestrator, OrchestratorError, ToolExecutionGateway,
)
from inneros_meta_guardian.selfheal_lab import (
    SelfHealingLab, LabError, case_evidence,
)


class SelfHealingEvidenceTests(unittest.TestCase):
    def test_snapshot_does_not_call_external_services(self):
        with patch("urllib.request.urlopen", side_effect=AssertionError("no network")):
            data = case_evidence()
        self.assertEqual("HISTORICAL_SOURCE_BACKED_SNAPSHOT", data["truth"])
        self.assertEqual(4, data["original_ci"]["failed"])
        self.assertEqual(339, data["candidate_ci"]["passed"])
        self.assertEqual(380, data["pr256_candidate_ci"]["passed"])
        self.assertFalse(data["release"]["production_verified_healed"])
        self.assertFalse(data["release"]["wonder_chat_mcp_wired"])
        self.assertFalse(data["release"]["public_paid_call_enabled"])
        self.assertFalse(data["wonder"]["owner_approval_independently_verified"])
        self.assertIsNone(data["wonder"]["billing_verified_usd"])
        self.assertIn("OPERATOR_REPORTED", data["wonder"]["truth"])

    def test_public_case_evidence_redacts_private_model_storage_location(self):
        data = case_evidence()
        serialized = json.dumps(data, sort_keys=True)
        self.assertNotIn("/home/", serialized)
        self.assertNotIn("C:\\\\Users\\\\", serialized)
        self.assertEqual(
            "PRIVATE_LOCAL_VOLUME_REDACTED",
            data["local_qwen_diagnostic"]["weights_path"],
        )

    def test_four_diagnostic_cases_distinguish_code_from_tests(self):
        cases = case_evidence()["cases"]
        self.assertEqual(["F1", "F2", "F3", "F4"], [c["id"] for c in cases])
        self.assertEqual(2, len([c for c in cases if c["truth"] == "SOURCE_CODE_AND_CI_VERIFIED"]))
        self.assertEqual(2, len([c for c in cases if c["truth"] == "TEST_CONTRACT_ADJUSTMENT"]))
        pr256_cases = case_evidence()["pr256_cases"]
        self.assertEqual(["F5", "F6", "F7"], [c["id"] for c in pr256_cases])


class ContextCollectorAndOrchestratorTests(unittest.TestCase):
    def test_global_snapshot_is_sanitized_and_contains_six_domains(self):
        snap = build_global_snapshot()
        self.assertEqual(SNAPSHOT_SCHEMA, snap["schema"])
        self.assertEqual(64, len(snap["snapshot_sha256"]))
        sections = snap["sections"]
        for section in ("infrastructure", "ncp_coordination", "agents", "code", "history", "security"):
            self.assertIn(section, sections)
            self.assertIn("timestamp", sections[section])
            self.assertIn("source", sections[section])
        raw = json.dumps(snap, sort_keys=True)
        self.assertNotIn("/home/", raw)
        self.assertNotIn("Bearer ", raw)
        self.assertEqual("<INNEROS_HOST_HOME>/app", sanitize_value("/home/operator/app"))

    def test_orchestrator_executes_multi_turn_tool_loop_and_enforces_policies(self):
        orch = DiagnosticOrchestrator()
        session = orch.start_investigation(
            prompt="Investiga por qué InnerOS tiene tareas pendientes sin ejecutarse y por qué los workers no están tomando trabajo.",
            engine_mode="hybrid_comparison",
        )
        self.assertEqual("COMPLETED_VERIFIED", session["status"])
        self.assertEqual(6, len(session["tool_history"]))
        self.assertTrue(all(tc["status"] == "EXECUTED_OK" for tc in session["tool_history"]))
        self.assertGreaterEqual(len(session["decisions"]["hypotheses"]), 3)
        self.assertEqual(4, len(session["decisions"]["controlled_actions"]))

        # Verify loop detection
        loop_session = orch.start_investigation(
            prompt="Prueba loop repetido",
            engine_mode="hybrid_comparison",
        )
        self.assertEqual("HALTED_LOOP_DETECTED", loop_session["status"])

        # Verify unallowlisted tool rejection
        gw = ToolExecutionGateway()
        denied = gw.execute("shell_exec", {})
        self.assertFalse(denied["ok"])
        self.assertEqual("DENIED_POLICY", denied["status"])

        cancelled = orch.cancel_session(session["session_id"])
        self.assertEqual("CANCELLED", cancelled["status"])
        self.assertEqual(11, len(TOOL_SCHEMAS))


class SelfHealingLabTests(unittest.TestCase):
    def setUp(self):
        self.lab = SelfHealingLab()

    def test_cannot_skip_approval_or_mutate_state_out_of_order(self):
        item = self.lab.start()
        self.assertEqual("observed", item["status"])
        with self.assertRaises(LabError):
            self.lab.transition(item["id"], "apply_virtual_patch")
        unchanged = self.lab.evidence(item["id"])["lab"]
        self.assertEqual("observed", unchanged["status"])
        self.assertEqual(1, len(unchanged["events"]))
        self.assertEqual("claimed", unchanged["fixture"]["task_status"])

    def test_complete_synthetic_loop_has_valid_hash_chain_without_network(self):
        with patch("urllib.request.urlopen", side_effect=AssertionError("no Meta or Qwen API calls")):
            state = self.lab.start()
            sid = state["id"]
            state = self.lab.transition(sid, "diagnose")
            self.assertEqual("DETERMINISTIC_LOCAL_DIAGNOSTIC_NOT_QWEN", state["diagnosis"]["method"])
            state = self.lab.transition(sid, "replay_wonder")
            self.assertEqual("OPERATOR_REPORTED_NO_NEW_META_CALL", state["wonder"]["truth"])
            with self.assertRaisesRegex(LabError, "display name"):
                self.lab.transition(sid, "acknowledge_lab", actor="")
            state = self.lab.transition(sid, "acknowledge_lab", actor="Demo operator")
            self.assertFalse(state["approval"]["paid_inference_authorized"])
            self.assertFalse(state["approval"]["device_authorized"])
            state = self.lab.transition(sid, "apply_virtual_patch")
            self.assertEqual(0, state["patch"]["production_files_changed"])
            state = self.lab.transition(sid, "verify")
        self.assertEqual("verified", state["status"])
        self.assertTrue(state["verification"]["passed"])
        self.assertTrue(state["audit"]["valid"])
        self.assertEqual(6, state["audit"]["events"])
        self.assertEqual(64, len(state["audit"]["head_sha256"]))
        self.assertEqual("blocked_for_review", state["fixture"]["task_status"])
        exported = self.lab.evidence(sid)
        self.assertEqual("SIMULATED_REPLAY_NOT_LIVE_INNEROS", exported["truth"])
        self.assertEqual(6, len(exported["lab"]["events"]))
        self.assertIn("no local qwen or meta", exported["limitations"][1].lower())

    def test_replay_not_an_authenticated_owner_approval(self):
        state = self.lab.start()
        state = self.lab.transition(state["id"], "diagnose")
        state = self.lab.transition(state["id"], "replay_wonder")
        state = self.lab.transition(state["id"], "acknowledge_lab", actor="Auditor")
        self.assertEqual("LAB_ONLY_ACK_NOT_SIGNED_OWNER_GRANT", state["approval"]["truth"])
        self.assertNotIn("signature", state["approval"])

    def test_hash_chain_detects_tampered_event(self):
        initial = self.lab.start()
        sid = initial["id"]
        self.lab.transition(sid, "diagnose")
        forged = json.loads(json.dumps(self.lab.evidence(sid)["lab"]["events"]))
        self.assertTrue(self.lab._verify_chain(forged)["valid"])
        forged[0]["payload"]["synthetic_problem"] = "silently changed"
        self.assertFalse(self.lab._verify_chain(forged)["valid"])

    def test_unknown_session_and_unknown_scenario_fail_closed(self):
        with self.assertRaises(LabError):
            self.lab.start("real_device")
        with self.assertRaises(LabError):
            self.lab.transition("lab_not_found", "verify")
        with self.assertRaises(LabError):
            self.lab.evidence("lab_not_found")

    def test_parallel_replay_requests_do_not_double_transition(self):
        initial = self.lab.start()
        sid = initial["id"]
        replies = []
        def run():
            try:
                replies.append(self.lab.transition(sid, "diagnose")["status"])
            except LabError:
                replies.append("blocked")
        threads = [threading.Thread(target=run) for _ in range(5)]
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        self.assertEqual(1, replies.count("diagnosed"))
        self.assertEqual(4, replies.count("blocked"))
        self.assertEqual(2, self.lab.evidence(sid)["lab"]["audit"]["events"])

    def test_session_capacity_is_bounded(self):
        self.lab._sessions = {"dummy" + str(i): {} for i in range(100)}
        with self.assertRaises(LabError):
            self.lab.start()

if __name__ == "__main__":
    unittest.main()
