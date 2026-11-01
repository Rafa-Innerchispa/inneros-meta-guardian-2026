"""One-request Meta Muse Spark probe with durable, private forensic measurements.

Does not connect to customer infrastructure, use agents, or retry. Python stdlib only.
Use from an authenticated operator terminal, never expose through the judge HTTP server.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
from datetime import datetime, timezone
from urllib import error, request
from typing import Any

ENDPOINT = "https://api.meta.ai/v1/responses"
MODELS_ENDPOINT = "https://api.meta.ai/v1/models"
MODEL = "muse-spark-1.3"
MAX_OUTPUT_TOKENS = 192
MAX_RESPONSE_BYTES = 262144
SYNTHETIC_INPUT = (
    "FICTIONAL LAB DATA ONLY (not a customer or a live device): "
    "At T+00, a lab uplink monitor reports a missed heartbeat on one simulated link; "
    "the redundant path reports healthy. At T+05, the monitor responds again. "
    "No hardware fault has been independently confirmed. "
    "Give exactly four short sections: OBSERVATIONS, HYPOTHESES, UNCERTAINTY, "
    "SAFE NEXT STEP. Never suggest executing a device command. "
    "Keep the total visible response under 90 words."
)
ALLOWED_PROBE_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{2,39}$")
SAFE_RESPONSE_HEADERS = (
    "x-request-id", "x-ratelimit-limit-requests", "x-ratelimit-remaining-requests",
    "x-ratelimit-remaining-tokens", "retry-after", "content-type",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_private_json(path: Path, obj: Any) -> None:
    data = (json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def create_private_directory(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name != "nt":
        root.chmod(0o700)


def safe_headers(headers: Any) -> dict[str, str]:
    if not headers:
        return {}
    # Header names may vary in capitalization and be either mapping or Message.
    return {key: str(headers.get(key, ""))[:100]
            for key in SAFE_RESPONSE_HEADERS if headers.get(key)}


def provider_error(data: Any, secret: str) -> dict[str, str]:
    raw = data.get("error", {}) if isinstance(data, dict) else {}
    if not isinstance(raw, dict):
        raw = {"message": str(raw)}
    values = {}
    for field in ("type", "code", "message"):
        val = raw.get(field)
        if val is not None:
            s = str(val).replace(secret, "[REDACTED]") if secret else str(val)
            values[field] = s[:240]
    return values


def read_http(request_object: request.Request, key: str, *,
              transport: Any = None, timeout: int = 12) -> dict[str, Any]:
    opener = transport or request.urlopen
    started = time.perf_counter_ns()
    try:
        with opener(request_object, timeout=timeout) as response:
            status = int(getattr(response, "status", 200))
            headers = safe_headers(getattr(response, "headers", {}))
            content = response.read(MAX_RESPONSE_BYTES + 1)
    except error.HTTPError as exc:
        status = exc.code
        headers = safe_headers(exc.headers)
        content = exc.read(MAX_RESPONSE_BYTES + 1)
    except (OSError, error.URLError, ValueError) as exc:
        return {
            "http_status": None,
            "latency_ms": round((time.perf_counter_ns() - started) / 1e6, 3),
            "provider_data": None,
            "response_bytes": 0,
            "response_sha256": None,
            "response_headers": {},
            "transport_error": type(exc).__name__,
        }
    elapsed = round((time.perf_counter_ns() - started) / 1e6, 3)
    # Even error messages are never allowed to echo the authorization secret to disk.
    if len(content) > MAX_RESPONSE_BYTES:
        return {
            "http_status": status, "latency_ms": elapsed, "provider_data": None,
            "response_bytes": len(content), "response_sha256": sha256(content),
            "response_headers": headers, "transport_error": "RESPONSE_TOO_LARGE",
        }
    cleaned = content.replace(key.encode(), b"[REDACTED]") if key else content
    try:
        data = json.loads(cleaned.decode("utf-8"))
    except (ValueError, UnicodeError):
        data = None
    return {
        "http_status": status, "latency_ms": elapsed, "provider_data": data,
        "response_bytes": len(cleaned), "response_sha256": sha256(cleaned),
        "response_headers": headers, "transport_error": None,
    }


def output_text(provider: dict[str, Any]) -> str:
    parts = []
    for item in provider.get("output", []) or []:
        if not isinstance(item, dict):
            continue
        if item.get("type") != "message":
            continue
        for part in item.get("content", []) or []:
            if isinstance(part, dict) and part.get("type") == "output_text":
                text = part.get("text")
                if isinstance(text, str):
                    parts.append(text)
    return "\n".join(parts).strip()


def classify(http: dict[str, Any], key: str) -> dict[str, Any]:
    status = http["http_status"]
    payload = http.get("provider_data")
    if http["transport_error"]:
        return {"status": "NETWORK_ERROR", "reason": http["transport_error"],
                "provider_response_id": None, "model_output_text": None, "usage": {}}
    if status != 200:
        err = provider_error(payload, key)
        if status == 402:
            result = "BILLING_BLOCKED"
        elif status == 401:
            result = "KEY_REJECTED"
        elif status == 403:
            result = "PERMISSION_BLOCKED"
        else:
            result = "HTTP_ERROR"
        return {"status": result, "reason": err, "provider_response_id": None,
                "model_output_text": None, "usage": {}}
    if not isinstance(payload, dict):
        return {"status": "UNVERIFIED_RESPONSE", "reason": "NON_JSON_SUCCESS",
                "provider_response_id": None, "model_output_text": None, "usage": {}}
    rid = payload.get("id")
    txt = output_text(payload)
    usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
    if not isinstance(rid, str) or not rid.strip() or payload.get("status") != "completed" or not txt:
        return {"status": "UNVERIFIED_RESPONSE",
                "reason": "MISSING_PROVIDER_ID_COMPLETION_OR_TEXT",
                "provider_response_id": rid if isinstance(rid, str) else None,
                "model_output_text": txt or None, "usage": usage}
    return {
        "status": "REAL_SUCCESS", "reason": None, "provider_response_id": rid,
        "model_output_text": txt, "usage": usage,
    }


def run_auth_check(key: str, output_root: Path, *, transport: Any = None) -> dict[str, Any]:
    create_private_directory(output_root)
    timestamp = utc_now()
    if not key:
        return {"status": "NO_KEY", "timestamp": timestamp}
    req = request.Request(MODELS_ENDPOINT, headers={"Authorization": "Bearer " + key,
                                                     "Accept": "application/json"},
                          method="GET")
    response = read_http(req, key, transport=transport)
    data = response.pop("provider_data")
    model_ids = [m.get("id") for m in data.get("data", []) if isinstance(m, dict)] if isinstance(data, dict) else []
    status = response["http_status"]
    receipt = {
        "operation": "GET_MODELS_KEY_CHECK_NO_GENERATION",
        "timestamp": timestamp,
        "status": "AUTH_ENDPOINT_OK" if status == 200 else ("BILLING_BLOCKED" if status == 402 else "AUTH_FAILED"),
        "model_available": MODEL in model_ids if status == 200 else None,
        "returned_model_count": len(model_ids) if status == 200 else None,
        "provider_error": provider_error(data, key) if status != 200 else None,
        **response,
    }
    # Save each check individually; never overwrite or store the API key.
    check_name = "auth_" + str(time.time_ns())
    write_private_json(output_root / (check_name + ".json"), receipt)
    return receipt


def run_one_shot(key: str, probe_id: str, output_root: Path, *,
                 owner_authorized: bool = False, transport: Any = None) -> dict[str, Any]:
    if not owner_authorized:
        raise ValueError("One paid-capable request requires explicit --owner-authorized.")
    if not key:
        raise ValueError("MODEL_API_KEY is absent; no request attempted.")
    if not ALLOWED_PROBE_ID.fullmatch(probe_id):
        raise ValueError("Probe id must be 3–40 lowercase letters, numbers, - or _.")
    create_private_directory(output_root)
    dest = output_root / probe_id
    # No retry with the same id even on 402, timeout, or process interruption.
    dest.mkdir(mode=0o700, exist_ok=False)
    write_private_json(dest / "claim.json", {
        "probe_id": probe_id, "claimed_at": utc_now(), "request_budget": 1,
        "owner_authorized": True, "retries_allowed": 0,
        "environment": "SYNTHETIC_FIXTURE_ONLY",
    })
    request_body = {
        "model": MODEL, "max_output_tokens": MAX_OUTPUT_TOKENS,
        "store": False, "input": SYNTHETIC_INPUT,
    }
    request_bytes = json.dumps(request_body, ensure_ascii=False,
                               separators=(",", ":"), sort_keys=True).encode("utf-8")
    write_private_json(dest / "request.json", {
        "url": ENDPOINT, "method": "POST", "payload": request_body,
        "request_sha256": sha256(request_bytes), "request_bytes": len(request_bytes),
        "truth": "SYNTHETIC_FIXTURE_ONLY", "timestamp": utc_now(),
    })
    req = request.Request(
        ENDPOINT, data=request_bytes,
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        method="POST",
    )
    response = read_http(req, key, transport=transport)
    payload = response.pop("provider_data")
    classified = classify({**response, "provider_data": payload}, key)
    usage = classified["usage"]
    out_tokens = usage.get("output_tokens")
    latency_sec = response["latency_ms"] / 1000.0
    throughput = (round(out_tokens / latency_sec, 3)
                  if isinstance(out_tokens, int) and latency_sec > 0 else None)
    receipt = {
        "schema_version": "1",
        "probe_id": probe_id,
        "timestamp_completed": utc_now(),
        "truth": "REAL_PROVIDER_VERIFIED" if classified["status"] == "REAL_SUCCESS" else "NO_VERIFIED_MODEL_EXECUTION",
        "result": classified["status"],
        "reason": classified["reason"],
        "model_requested": MODEL,
        "model_returned": payload.get("model") if isinstance(payload, dict) else None,
        "provider_response_id": classified["provider_response_id"],
        "provider_completion_status": payload.get("status") if isinstance(payload, dict) else None,
        "model_output_text": classified["model_output_text"],
        "usage": usage,
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": out_tokens,
        "total_tokens": usage.get("total_tokens"),
        "request_latency_ms": response["latency_ms"],
        "output_tokens_per_wall_second": throughput,
        "throughput_note": "End-to-end estimate including reasoning and network time, NOT model decode speed",
        "request_sha256": sha256(request_bytes),
        "response_sha256": response["response_sha256"],
        "response_bytes": response["response_bytes"],
        "http_status": response["http_status"],
        "safe_response_headers": response["response_headers"],
        "transport_error": response["transport_error"],
        "cost_usd_provider_reported": None,
        "billing_check_required": True,
        "request_limit": 1, "automatic_retries": 0,
        "synthetic_data_only": True,
    }
    if payload is not None:
        write_private_json(dest / "provider_response.json", payload)
    write_private_json(dest / "receipt.json", receipt)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safe one-shot Meta Model API proof; never paste the API key into the command line.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check-key", action="store_true", help="GET /models; no inference tokens")
    mode.add_argument("--one-shot", action="store_true", help="One POST /responses; may require billing")
    parser.add_argument("--probe-id", help="Unique explicit experiment ID for one-shot mode")
    parser.add_argument("--owner-authorized", action="store_true", help="Owner approved exactly one generation")
    parser.add_argument("--record-dir", default="runtime/meta_trials",
                        help="Private, gitignored local evidence directory")
    args = parser.parse_args(argv)
    key = os.environ.get("MODEL_API_KEY", "")
    root = Path(args.record_dir)
    try:
        if args.check_key:
            result = run_auth_check(key, root)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result.get("status") == "AUTH_ENDPOINT_OK" else 2
        if not args.probe_id:
            parser.error("--probe-id required for --one-shot")
        result = run_one_shot(key, args.probe_id, root, owner_authorized=args.owner_authorized)
        # All raw responses are stored privately under runtime/, not pushed to GitHub.
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("result") == "REAL_SUCCESS" else 2
    except (FileExistsError, ValueError, OSError) as exc:
        print(json.dumps({"status": "NO_REQUEST_OR_DUPLICATE_PROBE", "reason": type(exc).__name__,
                          "detail": str(exc)[:180]}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
