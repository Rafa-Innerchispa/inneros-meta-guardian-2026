"""Unit tests for live infrastructure, verified memory, and VoiceOps evidence."""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from inneros_meta_guardian.integrations import (
    LiveInfrastructureClient,
    VerifiedMemoryClient,
    VoiceOpsRecordedReceipt,
    redact_sensitive_data,
)


class LiveInfrastructureClientTests(unittest.TestCase):
    def test_allowlist_validation(self):
        client = LiveInfrastructureClient()
        with self.assertRaises(ValueError):
            client.fetch_reading("untrusted_site", "network")
        with self.assertRaises(ValueError):
            client.fetch_reading("casa", "untrusted_category")

    @patch("urllib.request.urlopen")
    def test_successful_live_reading_normalization(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"ok": true, "site": "casa", "category": "network", "signals": [{"name": "wan_ping", "status": "up"}], "summary": {"signals_needing_review": 0}}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        client = LiveInfrastructureClient(base_url="https://mock.guardian")
        reading = client.fetch_reading("casa", "network")
        self.assertTrue(reading["ok"])
        self.assertEqual("LIVE_INFRASTRUCTURE_READING", reading["truth"])
        self.assertEqual("casa", reading["site"])
        self.assertEqual(64, len(reading["snapshot_digest"]))
        self.assertFalse(reading["physical_mutation_applied"])


class VerifiedMemoryClientTests(unittest.TestCase):
    def test_recall_facts_when_service_unavailable(self):
        client = VerifiedMemoryClient()
        facts = client.recall_facts("casa")
        self.assertEqual(1, len(facts))
        self.assertEqual("MEMORY_UNAVAILABLE", facts[0]["truth"])
        self.assertEqual("NONE", facts[0]["source"])
        self.assertIn("Cognitive Memory Unavailable", facts[0]["title"])

    def test_recall_facts_demo_fixture_mode(self):
        client = VerifiedMemoryClient()
        facts = client.recall_facts("casa", allow_static_fixture=True)
        self.assertGreater(len(facts), 0)
        for f in facts:
            self.assertIn("fact_id", f)
            self.assertIn("title", f)
            self.assertEqual("STATIC_DEMO_FIXTURE_NOT_LIVE_COGNEE", f["truth"])
            self.assertEqual("DEMO_FIXTURE_OFFLINE_ONLY", f["source"])
            self.assertIsNone(f["confidence"])

    def test_recall_facts_filtering_in_demo_mode(self):
        client = VerifiedMemoryClient()
        facts = client.recall_facts("casa", query="UPS", allow_static_fixture=True)
        self.assertEqual(1, len(facts))
        self.assertIn("APC Smart-UPS", facts[0]["fact"])

    def test_redaction_sanitizes_ips_and_secrets(self):
        raw = {
            "title": "Core Router",
            "ip": "192.168.1.1",
            "mac": "00:1A:2B:3C:4D:5E",
            "api_key": "supersecretkey123",
            "nested": ["Connect to 10.0.0.5", {"password": "pass"}],
        }
        clean = redact_sensitive_data(raw)
        self.assertEqual("10.x.x.x", clean["ip"])
        self.assertEqual("XX:XX:XX:XX:XX:XX", clean["mac"])
        self.assertEqual("[REDACTED_SECRET]", clean["api_key"])
        self.assertIn("10.x.x.x", clean["nested"][0])
        self.assertEqual("[REDACTED_SECRET]", clean["nested"][1]["password"])

    def test_build_safe_redacted_snapshot_allowlist(self):
        from inneros_meta_guardian.integrations import build_safe_redacted_snapshot
        dangerous_telemetry = {
            "site": "casa",
            "category": "network",
            "severity": "warning",
            "freshness": "fresh",
            "internal_secret_token": "SHOULD_NOT_LEAK",
            "customer_name": "Private Client Corp",
            "device_credentials": {"admin": "rootpassword"},
            "signals": [
                {
                    "name": "wan_ping",
                    "status": "nominal",
                    "latency_ms": 12.4,
                    "uncertainty": "low",
                    "private_snmp_community": "secret_public",
                    "internal_routing_table": {"192.168.1.0/24": "eth0"},
                }
            ],
        }
        safe = build_safe_redacted_snapshot(dangerous_telemetry)
        self.assertEqual("casa", safe["site"])
        self.assertEqual("network", safe["category"])
        self.assertNotIn("internal_secret_token", safe)
        self.assertNotIn("customer_name", safe)
        self.assertNotIn("device_credentials", safe)

        signal = safe["signals"][0]
        self.assertEqual("wan_ping", signal["name"])
        self.assertEqual("nominal", signal["status"])
        self.assertNotIn("private_snmp_community", signal)
        self.assertNotIn("internal_routing_table", signal)


class VoiceOpsRecordedReceiptTests(unittest.TestCase):
    def test_voiceops_receipt_integrity(self):
        receipt = VoiceOpsRecordedReceipt.get_verified_call_receipt()
        self.assertEqual("HISTORIC_RECORDED_VOICEOPS_CALL", receipt["truth"])
        self.assertEqual("SIP/2.0 200 OK (INVITE/ACK/BYE sequence completed)", receipt["signaling"])
        self.assertEqual(3853, receipt["media"]["outbound_rtp_packets"])
        self.assertEqual(9389, receipt["media"]["inbound_rtp_packets"])
        self.assertEqual(7, receipt["speech_pipeline"]["accepted_stt_turns"])
        self.assertFalse(receipt["governance"]["physical_mutation_authorized"])
        self.assertFalse(receipt["governance"]["physical_mutation_executed"])


if __name__ == "__main__":
    unittest.main()
