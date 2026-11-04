"""Unit tests for Provider Financial Controls, Fireworks, Baseten, and Modal Adapters."""
from __future__ import annotations

import json
import unittest

from inneros_meta_guardian.baseten_adapter import BasetenAdapter, BasetenError
from inneros_meta_guardian.fireworks_adapter import FireworksAdapter, FireworksError
from inneros_meta_guardian.modal_sandbox_adapter import ModalSandboxAdapter, ModalSandboxError
from inneros_meta_guardian.provider_finance import (
    FinancialGovernanceError,
    ProviderFinanceManager,
)


class ProviderFinanceAndAdaptersTests(unittest.TestCase):
    def setUp(self) -> None:
        self.finance = ProviderFinanceManager()

    def test_initial_financial_ledger(self) -> None:
        ledger = self.finance.get_ledger()
        self.assertIn("fireworks_ai", ledger)
        self.assertIn("baseten", ledger)
        self.assertIn("modal", ledger)
        self.assertIn("meta_model_api", ledger)
        self.assertIn("local_amd_rocm", ledger)
        self.assertIn("gpt6_astra", ledger)

        # Fireworks checks
        fw = ledger["fireworks_ai"]
        self.assertAlmostEqual(fw["available_balance_usd"], 20.30, places=2)
        self.assertFalse(fw["auto_reload_enabled"])
        self.assertEqual(fw["account_email"], "rafagye@gmail.com")
        self.assertEqual(fw["status"], "TESTED_LIVE")
        self.assertEqual(fw["proposed_test_budget_usd"], 1.00)

        # Baseten checks
        base = ledger["baseten"]
        self.assertAlmostEqual(base["available_balance_usd"], 5.00, places=2)
        self.assertEqual(base["extra_pools"]["tool_calls_available_usd"], 2.00)
        self.assertEqual(base["extra_pools"]["dedicated_inference_available_usd"], 0.0)
        self.assertEqual(base["status"], "TESTED_LIVE")

        # Modal checks
        modal = ledger["modal"]
        self.assertAlmostEqual(modal["available_balance_usd"], 1.00, places=2)
        self.assertEqual(modal["proposed_test_budget_usd"], 0.25)
        self.assertEqual(modal["status"], "TESTED_LIVE")

        # Astra checks
        astra = ledger["gpt6_astra"]
        self.assertEqual(astra["status"], "BLOCKED")

    def test_finance_manager_governance_rules(self) -> None:
        # 1. Local AMD is unmetered and always allowed
        res_local = self.finance.validate_pre_call("local_amd_rocm", estimated_cost_usd=0.0)
        self.assertTrue(res_local["allowed"])
        self.assertEqual(res_local["cost_usd"], 0.0)

        # 2. Blocked provider is denied immediately
        with self.assertRaises(FinancialGovernanceError) as ctx:
            self.finance.validate_pre_call("gpt6_astra", estimated_cost_usd=0.01)
        self.assertIn("PROVIDER_BLOCKED", str(ctx.exception))

        # 3. Missing owner grant token is denied
        with self.assertRaises(FinancialGovernanceError) as ctx:
            self.finance.validate_pre_call("fireworks_ai", estimated_cost_usd=0.05)
        self.assertIn("OWNER_GRANT_REQUIRED", str(ctx.exception))

        # 4. Exceeding per-call ceiling is denied even with grant
        with self.assertRaises(FinancialGovernanceError) as ctx:
            self.finance.validate_pre_call(
                "fireworks_ai",
                estimated_cost_usd=0.50,  # Ceiling is 0.25
                owner_grant_token="grant_valid_123",
            )
        self.assertIn("BUDGET_CEILING_EXCEEDED", str(ctx.exception))

        # 5. Valid call within budget with grant is approved
        res_fw = self.finance.validate_pre_call(
            "fireworks_ai",
            estimated_cost_usd=0.05,
            owner_grant_token="grant_valid_123",
        )
        self.assertTrue(res_fw["allowed"])

        # 6. Usage recording updates balance and issues receipt
        rcpt = self.finance.record_usage_receipt(
            provider_id="fireworks_ai",
            actual_cost_usd=0.02,
            prompt_tokens=100,
            completion_tokens=50,
        )
        self.assertEqual(rcpt["actual_cost_usd"], 0.02)
        self.assertAlmostEqual(rcpt["post_balance_usd"], 20.28, places=2)
        self.assertTrue(rcpt["receipt_digest"])

    def test_fireworks_adapter(self) -> None:
        adapter = FireworksAdapter(finance_manager=self.finance)

        # Supported models
        models = adapter.get_supported_models()
        self.assertIn("accounts/fireworks/models/llama-v3p3-70b-instruct", models)
        self.assertIn("accounts/fireworks/models/llama-v3p1-8b-instruct", models)

        # Empty payload fails
        with self.assertRaises(FireworksError):
            adapter.complete(messages=[])

        # Dry run contract
        dry = adapter.complete(
            messages=[{"role": "user", "content": "Analyze incident"}],
            dry_run=True,
        )
        self.assertTrue(dry["ok"])
        self.assertEqual(dry["status"], "DRY_RUN_CONTRACT_VALID")
        self.assertGreater(dry["estimated_cost_usd"], 0.0)

        # Mock contract verification
        mock_resp = {
            "id": "fw_mock_123",
            "choices": [{"message": {"role": "assistant", "content": "Incident analyzed."}}],
            "usage": {"prompt_tokens": 80, "completion_tokens": 20},
        }
        res_mock = adapter.complete(
            messages=[{"role": "user", "content": "Analyze incident"}],
            mock_response=mock_resp,
        )
        self.assertTrue(res_mock["ok"])
        self.assertEqual(res_mock["status"], "MOCK_CONTRACT_VERIFIED")
        self.assertIsNotNone(res_mock["receipt"])

        # Without grant, live attempt fails closed
        with self.assertRaises(FireworksError) as ctx:
            adapter.complete(messages=[{"role": "user", "content": "Live call"}])
        self.assertIn("OWNER_GRANT_REQUIRED", str(ctx.exception))

    def test_baseten_adapter(self) -> None:
        adapter = BasetenAdapter(finance_manager=self.finance)

        # Supported models
        models = adapter.get_supported_models()
        self.assertIn("meta-models/muse-spark-open", models)

        # Dry run contract
        dry = adapter.complete(
            messages=[{"role": "user", "content": "Inspect worktree"}],
            is_tool_call=True,
            dry_run=True,
        )
        self.assertTrue(dry["ok"])
        self.assertEqual(dry["pool"], "tool_calls_available_usd")

        # Mock contract verification
        mock_resp = {
            "id": "baseten_mock_123",
            "choices": [{"message": {"role": "assistant", "content": "Worktree verified."}}],
            "usage": {"prompt_tokens": 120, "completion_tokens": 40},
        }
        res_mock = adapter.complete(
            messages=[{"role": "user", "content": "Inspect worktree"}],
            is_tool_call=True,
            mock_response=mock_resp,
        )
        self.assertTrue(res_mock["ok"])
        self.assertEqual(res_mock["pool"], "tool_calls_available_usd")

        # Live attempt without grant fails closed
        with self.assertRaises(BasetenError) as ctx:
            adapter.complete(messages=[{"role": "user", "content": "Live call"}])
        self.assertIn("BASETEN_GOVERNANCE_BLOCKED", str(ctx.exception))

    def test_modal_sandbox_adapter(self) -> None:
        adapter = ModalSandboxAdapter(finance_manager=self.finance)

        spec = adapter.get_sandbox_spec()
        self.assertEqual(spec["compute"], "CPU_ONLY")
        self.assertIsNone(spec["gpu"])
        self.assertFalse(spec["persistent"])
        self.assertEqual(spec["network_isolation"], "NO_LAN_ACCESS")
        self.assertEqual(spec["destruction_policy"], "DESTROY_ON_EXIT")

        # Timeout over 60s rejected
        with self.assertRaises(ModalSandboxError) as ctx:
            adapter.run_isolated_test(
                test_script_content="pytest",
                files_manifest={"test.py": "def test(): pass"},
                timeout_seconds=90,
            )
        self.assertIn("TIMEOUT_EXCEEDED", str(ctx.exception))

        # Dry run contract
        dry = adapter.run_isolated_test(
            test_script_content="pytest",
            files_manifest={"test_ops.py": "def test(): pass"},
            dry_run=True,
        )
        self.assertTrue(dry["ok"])
        self.assertEqual(dry["status"], "DRY_RUN_CONTRACT_VALID")
        self.assertTrue(dry["destruction_on_exit"])

        # Mock sandbox verification
        mock_out = {"exit_code": 0, "tests_passed": 10, "duration_seconds": 15}
        res_mock = adapter.run_isolated_test(
            test_script_content="pytest",
            files_manifest={"test_ops.py": "def test(): pass"},
            mock_output=mock_out,
        )
        self.assertTrue(res_mock["ok"])
        self.assertEqual(res_mock["status"], "MOCK_CONTRACT_VERIFIED")
        self.assertIsNotNone(res_mock["receipt"])

    def test_financial_matrix_summary(self) -> None:
        matrix = self.finance.generate_financial_matrix()
        self.assertEqual(matrix["schema"], "inneros.provider_financial_matrix.v1")
        self.assertGreater(matrix["total_external_available_usd"], 25.0)
        self.assertEqual(matrix["unapproved_cloud_spend_usd"], 0.0)
        self.assertIn("fireworks_ai", matrix["providers"])
        self.assertIn("baseten", matrix["providers"])
        self.assertIn("modal", matrix["providers"])

    def test_web_finance_and_dossier_routes(self) -> None:
        import urllib.request
        from http.server import ThreadingHTTPServer
        import threading
        from inneros_meta_guardian.web import Handler, Guardian

        class TestH(Handler):
            pass

        guardian = Guardian("runtime/test_finance.db")
        TestH.guardian = guardian
        server = ThreadingHTTPServer(("127.0.0.1", 8989), TestH)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        try:
            # 1. GET /api/meta/finance
            with urllib.request.urlopen("http://127.0.0.1:8989/api/meta/finance") as resp:
                data = json.loads(resp.read().decode())
                self.assertEqual(resp.status, 200)
                self.assertIn("providers", data)
                self.assertIn("fireworks_ai", data["providers"])

            # 2. GET /api/meta/dossier
            with urllib.request.urlopen("http://127.0.0.1:8989/api/meta/dossier") as resp:
                dossier = json.loads(resp.read().decode())
                self.assertEqual(resp.status, 200)
                self.assertIn("domains", dossier)

            # 3. POST /api/meta/finance/dryrun
            req = urllib.request.Request(
                "http://127.0.0.1:8989/api/meta/finance/dryrun",
                data=json.dumps({"provider": "fireworks_ai"}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req) as resp:
                dry = json.loads(resp.read().decode())
                self.assertEqual(resp.status, 200)
                self.assertTrue(dry["ok"])
                self.assertEqual(dry["status"], "DRY_RUN_CONTRACT_VALID")
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
