"""Unit tests for Meta Ecosystem Catalog, Adapters, and Repair Benchmark Evaluator."""
from __future__ import annotations

import unittest

from inneros_meta_guardian.meta_image import MetaImageClient, MetaImageError
from inneros_meta_guardian.meta_once import OneShotGrantStore
from inneros_meta_guardian.meta_registry import META_CATALOG, MetaProviderRegistry
from inneros_meta_guardian.meta_spark import MetaSparkClient, MetaSparkError
from inneros_meta_guardian.meta_voice import MetaVoiceClient, MetaVoiceError
from inneros_meta_guardian.repair_evaluator import RepairEvaluator


class MetaCatalogAndAdaptersTests(unittest.TestCase):
    def setUp(self) -> None:
        self.grant_store = OneShotGrantStore()

    def test_registry_catalog_integrity(self) -> None:
        providers = MetaProviderRegistry.list_providers()
        self.assertGreaterEqual(len(providers), 9)

        # Check Qwen
        qwen = MetaProviderRegistry.get_provider("local_qwen3_coder_30b")
        self.assertIsNotNone(qwen)
        self.assertEqual(qwen["status"], "TESTED")
        self.assertFalse(qwen["requires_owner_grant"])
        self.assertIn("Radeon", qwen["display_name"])

        # Check Muse Wonder
        wonder = MetaProviderRegistry.get_provider("muse_wonder_1_0")
        self.assertIsNotNone(wonder)
        self.assertEqual(wonder["status"], "TESTED")
        self.assertTrue(wonder["requires_owner_grant"])

        # Check Muse Code CLI
        code = MetaProviderRegistry.get_provider("muse_code_1_4")
        self.assertIsNotNone(code)
        self.assertEqual(code["status"], "INSTALLED")

        # Check Argon Comparative
        argon = MetaProviderRegistry.get_provider("argon_comparative")
        self.assertIsNotNone(argon)
        self.assertEqual(argon["status"], "TESTED")

        # Check GPT-6 Astra
        astra = MetaProviderRegistry.get_provider("gpt6_astra")
        self.assertIsNotNone(astra)
        self.assertEqual(astra["status"], "BLOCKED")
        self.assertEqual(astra["availability"], "BLOCKED_API_ACCESS")

        # Check summary counts
        summary = MetaProviderRegistry.get_ecosystem_summary()
        self.assertGreaterEqual(summary["total_catalog_models"], 9)
        self.assertGreaterEqual(summary["tested_and_ready"], 3)

    def test_spark_adapter_governance(self) -> None:
        client = MetaSparkClient(grant_store=self.grant_store)

        # Empty prompt fails
        with self.assertRaises(MetaSparkError):
            client.invoke(prompt="")

        # Missing grant token is blocked
        with self.assertRaises(MetaSparkError) as ctx:
            client.invoke(prompt="Analyze timeout")
        self.assertIn("MUSE_SPARK_BLOCKED", str(ctx.exception))

        # Invalid grant token fails
        with self.assertRaises(MetaSparkError) as ctx:
            client.invoke(prompt="Analyze timeout", grant_token="grant_invalid_token")
        self.assertIn("MUSE_SPARK_GRANT_INVALID", str(ctx.exception))

        # Mock contract verified without live network
        res = client.invoke(
            prompt="Analyze lock contention",
            mock_response={"analysis": "Deadlock in claim lease"},
        )
        self.assertTrue(res["ok"])
        self.assertEqual(res["status"], "MOCK_CONTRACT_VERIFIED")
        self.assertEqual(res["model"], "muse-spark-1.3")

    def test_image_adapter_governance(self) -> None:
        client = MetaImageClient(grant_store=self.grant_store)

        # Empty prompt fails
        with self.assertRaises(MetaImageError):
            client.generate_creative_asset(prompt="")

        # Invalid resolution fails
        with self.assertRaises(MetaImageError):
            client.generate_creative_asset(prompt="Server rack", resolution="999x999")

        # Missing grant token is blocked
        with self.assertRaises(MetaImageError) as ctx:
            client.generate_creative_asset(prompt="Rack switch diagram")
        self.assertIn("MUSE_IMAGE_BLOCKED", str(ctx.exception))

        # Mock contract verified
        res = client.generate_creative_asset(
            prompt="Rack switch diagram",
            resolution="1024x1024",
            mock_output_path="/tmp/mock_switch.png",
        )
        self.assertTrue(res["ok"])
        self.assertEqual(res["status"], "MOCK_CONTRACT_VERIFIED")
        self.assertEqual(res["asset_path"], "/tmp/mock_switch.png")

    def test_voice_adapter_governance(self) -> None:
        client = MetaVoiceClient(grant_store=self.grant_store)

        # Invalid audio format fails
        with self.assertRaises(MetaVoiceError):
            client.transcribe_audio_snippet(audio_format="exe")

        # Missing audio bytes fails
        with self.assertRaises(MetaVoiceError):
            client.transcribe_audio_snippet(audio_bytes=None)

        # Missing grant token is blocked
        with self.assertRaises(MetaVoiceError) as ctx:
            client.transcribe_audio_snippet(audio_bytes=b"RIFF...", audio_format="wav")
        self.assertIn("MUSE_VOICE_BLOCKED", str(ctx.exception))

        # Mock transcript contract verified
        res = client.transcribe_audio_snippet(
            audio_format="wav",
            mock_transcript="Alerta, switch de fibra óptica en falla",
        )
        self.assertTrue(res["ok"])
        self.assertEqual(res["status"], "MOCK_CONTRACT_VERIFIED")
        self.assertEqual(res["transcript"], "Alerta, switch de fibra óptica en falla")

    def test_repair_evaluator_data(self) -> None:
        comp = RepairEvaluator.get_benchmark_comparison()
        self.assertEqual(comp.get("schema"), "inneros.repair_benchmark_comparison.v1")

        problem = comp.get("benchmark_problem", {})
        self.assertIn("9 FAILED", problem.get("failing_tests_before", ""))
        self.assertEqual(problem.get("baseline_commit"), "beccbd495dc2ab33e5c8cf3abe5fa988047cc15f")

        argon = comp.get("argon_repair", {})
        self.assertEqual(argon.get("status"), "VERIFIED_PASS")
        self.assertIn("10 PASSED", argon.get("tests_after", ""))
        self.assertIn("94d90d34", argon.get("commit_sha", ""))

        muse = comp.get("muse_code_repair", {})
        self.assertEqual(muse.get("auth_frontier_status"), "BLOCKED_AWAITING_OWNER_AUTH")
        self.assertEqual(muse.get("msp_events_logged"), 40)

        inventory = RepairEvaluator.get_ecosystem_inventory()
        self.assertIn("components", inventory)
        self.assertGreaterEqual(len(inventory["components"]), 11)


if __name__ == "__main__":
    unittest.main()
