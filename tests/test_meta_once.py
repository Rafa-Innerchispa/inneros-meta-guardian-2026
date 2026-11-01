"""Unit tests for Meta Muse Spark 1.3 one-shot grant lifecycle and operator."""
from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock, patch

from inneros_meta_guardian.meta_once import (
    GRANT_STORE,
    GrantError,
    MetaOnceOperator,
    OneShotGrantStore,
)


class OneShotGrantTests(unittest.TestCase):
    def setUp(self):
        self.store = OneShotGrantStore()
        self.valid_digest = "a" * 64

    def test_create_and_consume_grant_happy_path(self):
        grant = self.store.create_grant(self.valid_digest, ttl_seconds=60)
        self.assertTrue(grant["token"].startswith("grant_"))
        self.assertFalse(grant["consumed"])

        consumed = self.store.consume_grant(grant["token"], self.valid_digest)
        self.assertTrue(consumed["consumed"])
        self.assertIsNotNone(consumed["consumed_at"])

    def test_replay_prevention_fails_on_second_consumption(self):
        grant = self.store.create_grant(self.valid_digest, ttl_seconds=60)
        self.store.consume_grant(grant["token"], self.valid_digest)

        with self.assertRaises(GrantError) as ctx:
            self.store.consume_grant(grant["token"], self.valid_digest)
        self.assertIn("ALREADY been consumed", str(ctx.exception))

    def test_digest_mismatch_rejected(self):
        grant = self.store.create_grant(self.valid_digest, ttl_seconds=60)
        with self.assertRaises(GrantError) as ctx:
            self.store.consume_grant(grant["token"], "b" * 64)
        self.assertIn("snapshot_digest mismatch", str(ctx.exception))

    def test_expired_grant_rejected(self):
        grant = self.store.create_grant(self.valid_digest, ttl_seconds=-10)
        with self.assertRaises(GrantError) as ctx:
            self.store.consume_grant(grant["token"], self.valid_digest)
        self.assertIn("expired", str(ctx.exception))


class MetaOnceOperatorTests(unittest.TestCase):
    def setUp(self):
        self.digest = "c" * 64
        self.grant = GRANT_STORE.create_grant(self.digest, ttl_seconds=120)
        self.incident = {
            "site": "casa",
            "category": "network",
            "signals": [{"name": "wan_ping", "status": "up"}],
            "snapshot_digest": self.digest,
        }
        self.memory = [{"title": "Dual-node", "fact": "Nominal router", "confidence": 0.99}]

    def test_meta_operator_returns_not_run_when_key_absent(self):
        operator = MetaOnceOperator(api_key="")
        receipt = operator.execute_inference(self.grant["token"], self.incident, self.memory)

        self.assertTrue(receipt["ok"])
        self.assertEqual("NOT_RUN", receipt["status"])
        self.assertEqual("MODEL_API_KEY_ABSENT_OR_CREDITS_PENDING", receipt["reason"])
        self.assertTrue(receipt["local_fallback_applied"])
        self.assertIn("observations", receipt["analysis"])
        self.assertIn("recommended_action", receipt["analysis"])

    @patch("urllib.request.urlopen")
    def test_meta_operator_live_success_with_key(self, mock_urlopen):
        # Mock Meta Responses API payload
        meta_response = {
            "id": "resp_meta_12345",
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": "OBSERVATIONS: Wan ping nominal. HYPOTHESES: Normal state. UNCERTAINTY: None. RECOMMENDED ACTION: Maintain monitoring.",
                        }
                    ],
                }
            ],
            "usage": {"total_tokens": 128},
        }
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(meta_response).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        fresh_grant = GRANT_STORE.create_grant(self.digest, ttl_seconds=120)
        operator = MetaOnceOperator(api_key="mock_secret_key_from_vault")
        receipt = operator.execute_inference(fresh_grant["token"], self.incident, self.memory)

        self.assertTrue(receipt["ok"])
        self.assertEqual("REAL", receipt["status"])
        self.assertEqual("resp_meta_12345", receipt["response_id"])
        self.assertEqual(128, receipt["tokens_used"])
        self.assertFalse(receipt["local_fallback_applied"])
        self.assertIn("Maintain monitoring", receipt["raw_text"])


if __name__ == "__main__":
    unittest.main()
