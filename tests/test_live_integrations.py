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
    def test_recall_facts_for_casa(self):
        client = VerifiedMemoryClient()
        facts = client.recall_facts("casa")
        self.assertGreater(len(facts), 0)
        for f in facts:
            self.assertIn("fact_id", f)
            self.assertIn("title", f)
            self.assertIn("confidence", f)

    def test_recall_facts_filtering(self):
        client = VerifiedMemoryClient()
        facts = client.recall_facts("casa", query="UPS")
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
