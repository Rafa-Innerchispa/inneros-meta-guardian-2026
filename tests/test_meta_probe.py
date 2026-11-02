"""Offline tests for the first-use Meta API key and synthetic one-shot probe."""
from __future__ import annotations

from io import BytesIO
import json
import os
from pathlib import Path
import tempfile
import unittest
from urllib import error

from inneros_meta_guardian.meta_probe import (
    ENDPOINT, MODEL, MAX_OUTPUT_TOKENS, SYNTHETIC_INPUT,
    run_auth_check, run_one_shot,
)


class FakeResponse:
    def __init__(self, obj, status=200, headers=None):
        self.status = status
        self.headers = headers or {}
        self.buf = json.dumps(obj).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, count=-1):
        if count == -1:
            return self.buf
        data = self.buf[:count]
        self.buf = self.buf[count:]
        return data


class MetaProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "runtime"
        self.key = "test_key_only_never_real"

    def tearDown(self):
        self.tmp.cleanup()

    def test_missing_key_auth_has_no_network_call(self):
        result = run_auth_check("", self.root, transport=lambda *a, **k: self.fail("called network"))
        self.assertEqual("NO_KEY", result["status"])

    def test_auth_check_get_models_without_generation(self):
        requests = []
        def transport(req, timeout):
            requests.append(req)
            self.assertEqual("GET", req.get_method())
            self.assertTrue(req.full_url.endswith("/models"))
            return FakeResponse({"data": [{"id": MODEL}]})
        result = run_auth_check(self.key, self.root, transport=transport)
        self.assertEqual("AUTH_ENDPOINT_OK", result["status"])
        self.assertTrue(result["model_available"])
        self.assertEqual(1, len(requests))
        saved = list(self.root.glob("auth_*.json"))
        self.assertEqual(1, len(saved))
        self.assertNotIn(self.key, saved[0].read_text("utf-8"))

    def test_auth_check_payment_required_is_not_success(self):
        def transport(req, timeout):
            raise error.HTTPError(req.full_url, 402, "Payment Required", {},
                                  BytesIO(b'{"error":{"code":"billing_not_configured","type":"billing_error"}}'))
        result = run_auth_check(self.key, self.root, transport=transport)
        self.assertEqual("BILLING_BLOCKED", result["status"])
        self.assertEqual(402, result["http_status"])

    def test_one_real_complete_receipt_records_all_metrics_privately(self):
        reqs = []
        provider = {
            "id": "resp_actual_provider_test",
            "status": "completed",
            "model": MODEL,
            "output": [{"type": "message", "content": [
                {"type": "output_text", "text": "OBSERVATIONS: One synthetic heartbeat missed.\n"
                  "UNCERTAINTY: No hardware fault proven."}]}],
            "usage": {"input_tokens": 70, "output_tokens": 110, "total_tokens": 180},
        }
        def transport(req, timeout):
            reqs.append(req)
            self.assertEqual("POST", req.get_method())
            self.assertEqual(ENDPOINT, req.full_url)
            payload = json.loads(req.data)
            self.assertEqual(MODEL, payload["model"])
            self.assertEqual(MAX_OUTPUT_TOKENS, payload["max_output_tokens"])
            self.assertEqual(False, payload["store"])
            self.assertEqual(SYNTHETIC_INPUT, payload["input"])
            self.assertIn("FICTIONAL LAB DATA ONLY", payload["input"])
            return FakeResponse(provider, headers={"x-request-id": "meta-req-test"})
        r = run_one_shot(self.key, "billing-probe-001", self.root,
                         owner_authorized=True, transport=transport)
        self.assertEqual("REAL_SUCCESS", r["result"])
        self.assertEqual("REAL_PROVIDER_VERIFIED", r["truth"])
        self.assertEqual(180, r["total_tokens"])
        self.assertEqual(70, r["input_tokens"])
        self.assertEqual(110, r["output_tokens"])
        self.assertEqual("resp_actual_provider_test", r["provider_response_id"])
        self.assertIsNotNone(r["request_latency_ms"])
        self.assertEqual(1, len(reqs))
        folder = self.root / "billing-probe-001"
        self.assertTrue((folder / "provider_response.json").exists())
        self.assertTrue((folder / "receipt.json").exists())
        self.assertTrue((folder / "request.json").exists())
        self.assertTrue((folder / "claim.json").exists())
        for file in folder.iterdir():
            self.assertNotIn(self.key, file.read_text("utf-8"))
            if os.name == "posix":
                self.assertEqual(0o600, file.stat().st_mode & 0o777)
        with self.assertRaises(FileExistsError):
            run_one_shot(self.key, "billing-probe-001", self.root,
                         owner_authorized=True, transport=transport)
        self.assertEqual(1, len(reqs))

    def test_payment_402_single_request_persisted_no_retry(self):
        count = []
        def transport(req, timeout):
            count.append(1)
            raise error.HTTPError(req.full_url, 402, "Payment Required",
                {"x-request-id": "req_402"}, BytesIO(json.dumps({
                    "error": {"type": "billing_error", "code": "billing_not_configured",
                              "message": "Add a payment method."}
                }).encode("utf-8")))
        r = run_one_shot(self.key, "no-card-001", self.root,
                         owner_authorized=True, transport=transport)
        self.assertEqual("BILLING_BLOCKED", r["result"])
        self.assertEqual(402, r["http_status"])
        self.assertEqual("billing_not_configured", r["reason"]["code"])
        self.assertIsNone(r["provider_response_id"])
        self.assertEqual(1, len(count))
        with self.assertRaises(FileExistsError):
            run_one_shot(self.key, "no-card-001", self.root,
                         owner_authorized=True, transport=transport)
        self.assertEqual(1, len(count))

    def test_response_without_authentic_id_is_not_real(self):
        def transport(req, timeout):
            return FakeResponse({"status": "completed", "output": [
                {"type": "message", "content": [{"type": "output_text", "text": "fake response"}]}]})
        r = run_one_shot(self.key, "missing-id-001", self.root,
                         owner_authorized=True, transport=transport)
        self.assertEqual("UNVERIFIED_RESPONSE", r["result"])
        self.assertEqual("NO_VERIFIED_MODEL_EXECUTION", r["truth"])
        self.assertIsNone(r["provider_response_id"])

    def test_incomplete_provider_response_is_not_real(self):
        def transport(req, timeout):
            return FakeResponse({
                "id": "resp_x",
                "status": "incomplete",
                "incomplete_details": {"reason": "max_output_tokens"},
                "output": [],
                "usage": {"input_tokens": 108, "output_tokens": 192, "total_tokens": 300,
                          "output_tokens_details": {"reasoning_tokens": 190}},
            })
        r = run_one_shot(self.key, "incomplete-001", self.root,
                         owner_authorized=True, transport=transport)
        self.assertEqual("INCOMPLETE_MODEL_RESPONSE", r["result"])
        self.assertEqual("INCOMPLETE_MODEL_RESPONSE", r["truth"])
        self.assertEqual(190, r["reasoning_tokens"])
        self.assertIsNone(r["model_output_text"])

    def test_one_shot_custom_budget_and_reasoning_effort(self):
        reqs = []
        def transport(req, timeout):
            reqs.append(req)
            payload = json.loads(req.data)
            self.assertEqual(512, payload["max_output_tokens"])
            self.assertEqual({"effort": "medium"}, payload["reasoning"])
            return FakeResponse({
                "id": "resp_custom",
                "status": "completed",
                "output": [{"type": "message", "content": [{"type": "output_text", "text": "VERIFIED"}]}],
                "usage": {"input_tokens": 80, "output_tokens": 200, "total_tokens": 280,
                          "output_tokens_details": {"reasoning_tokens": 120}},
            })
        r = run_one_shot(self.key, "custom-001", self.root, owner_authorized=True,
                         max_output_tokens=512, reasoning_effort="medium", transport=transport)
        self.assertEqual("REAL_SUCCESS", r["result"])
        self.assertEqual(120, r["reasoning_tokens"])
        self.assertEqual(1, len(reqs))

    def test_one_shot_rejects_tokens_above_1024(self):
        with self.assertRaises(ValueError):
            run_one_shot(self.key, "invalid-tok-001", self.root, owner_authorized=True,
                         max_output_tokens=2048, transport=lambda *a, **k: self.fail("network"))

    def test_no_paid_call_without_explicit_owner_authorization(self):
        with self.assertRaises(ValueError):
            run_one_shot(self.key, "not-authorized-001", self.root,
                         owner_authorized=False, transport=lambda *a, **k: self.fail("NETWORK"))
        self.assertFalse(self.root.exists())

    def test_no_paid_call_when_key_missing(self):
        with self.assertRaises(ValueError):
            run_one_shot("", "no-key-001", self.root,
                         owner_authorized=True, transport=lambda *a, **k: self.fail("NETWORK"))

    def test_invalid_probe_id_rejected_before_network_or_writes(self):
        with self.assertRaises(ValueError):
            run_one_shot(self.key, "../private-key", self.root,
                         owner_authorized=True, transport=lambda *a, **k: self.fail("NETWORK"))
        self.assertFalse(self.root.exists())


if __name__ == "__main__":
    unittest.main()

