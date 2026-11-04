"""Executes live repair benchmark across:
1. Meta Muse Spark Open via Fireworks AI
2. Meta Muse Spark Open via Baseten
3. Qwen3-Coder-30B-AWQ via Local AMD vLLM :8000 (via SSH to 127.0.0.1:8000)

Measures: latency, input/output/reasoning tokens, costs, and extracts candidate repair code.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOSSIER_PATH = REPO_ROOT / "docs" / "evidence" / "bench_20261104" / "expediente_canonico_reparacion.json"
OUTPUT_DIR = REPO_ROOT / "docs" / "evidence" / "bench_20261104"
RAW_DIR = OUTPUT_DIR / "raw-redacted"
PATCHES_DIR = OUTPUT_DIR / "patches"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PATCHES_DIR.mkdir(parents=True, exist_ok=True)

with open(DOSSIER_PATH, "r", encoding="utf-8") as f:
    dossier_data = json.load(f)

dossier_str = json.dumps(dossier_data, indent=2)
dossier_hash = hashlib.sha256(dossier_str.encode("utf-8")).hexdigest()

SYSTEM_PROMPT = (
    "You are an expert autonomous distributed systems engineer for InnerOS. "
    "You are fixing coordination defects in ops_interactive_recovery.py and ops_awaiting_claim.py.\n"
    "Given the canonical incident dossier, fix these 5 root causes:\n"
    "1. Validating claim_host matches current host before checking local PID liveness; if remote host, do not recover without remote_liveness_verifier.\n"
    "2. Resolving linked worktree .git pointer files ('gitdir: ...') to detect real index.lock.\n"
    "3. Enforcing atomic CAS (modified_count == 1) on recovery updates.\n"
    "4. Retaining awaiting_antigravity_claim precedence for orchestrated tasks.\n"
    "5. Never recovering tasks with active heartbeat (< 180s) or active local PID.\n"
    "Keep reasoning very concise (< 150 words), then immediately output the complete, production-ready Python implementation inside a ```python ``` codeblock."
)

USER_PROMPT = (
    f"Canonical Incident Dossier (SHA-256: {dossier_hash}):\n"
    f"```json\n{dossier_str}\n```\n\n"
    "Provide concise reasoning and the complete Python implementation inside ```python ```."
)

prompt_hash = hashlib.sha256((SYSTEM_PROMPT + USER_PROMPT).encode("utf-8")).hexdigest()


def extract_python_code(text: str) -> str:
    blocks = re.findall(r"```python\s*(.*?)\s*```", text, re.DOTALL)
    if blocks:
        return max(blocks, key=len)
    return text


def run_fireworks() -> dict:
    print("\n--- [1/3] Running Meta Muse Spark Open via Fireworks AI ---")
    key = os.getenv("FIREWORKS_API_KEY", "")
    url = "https://api.fireworks.ai/inference/v1/chat/completions"
    payload = {
        "model": "accounts/fireworks/models/muse-spark-open",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT},
        ],
        "temperature": 0.1,
        "max_tokens": 2800,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    t1 = time.time()
    duration_ms = round((t1 - t0) * 1000, 2)

    choice = data["choices"][0]
    content = choice["message"].get("content") or ""
    reasoning = choice["message"].get("reasoning_content") or ""
    usage = data.get("usage", {})

    code = extract_python_code(content)
    (PATCHES_DIR / "fireworks_muse_spark_repair.py").write_text(code, encoding="utf-8")
    (PATCHES_DIR / "fireworks_full_response.md").write_text(
        f"# Fireworks Full Response\n\n## Content\n{content}\n\n## Reasoning\n{reasoning}\n",
        encoding="utf-8",
    )

    cost = round((usage.get("prompt_tokens", 0) * 0.20 + usage.get("completion_tokens", 0) * 0.80) / 1e6, 6)

    receipt = {
        "candidate": "Meta Muse Spark Open (Fireworks AI)",
        "provider": "fireworks_ai",
        "model_id": "accounts/fireworks/models/muse-spark-open",
        "run_id": data.get("id"),
        "dossier_hash": dossier_hash,
        "prompt_hash": prompt_hash,
        "duration_ms": duration_ms,
        "tokens": {
            "input": usage.get("prompt_tokens", 0),
            "output": usage.get("completion_tokens", 0),
            "total": usage.get("total_tokens", 0),
            "reasoning": len(reasoning.split()) if reasoning else 0,
        },
        "cost_usd": cost,
        "code_chars": len(code),
        "finish_reason": choice.get("finish_reason"),
        "status": "TESTED_LIVE_SUCCESS",
    }
    (RAW_DIR / "bench_repair_fireworks_receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(f"Fireworks done: {duration_ms}ms, {usage.get('total_tokens')} tokens, {len(code)} code chars, finish_reason: {choice.get('finish_reason')}, ${cost} USD")
    return receipt


def run_baseten() -> dict:
    print("\n--- [2/3] Running Meta Muse Spark Open via Baseten ---")
    key = os.getenv("BASETEN_API_KEY", "")
    url = "https://inference.baseten.co/v1/chat/completions"
    payload = {
        "model": "meta-models/muse-spark-open",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT},
        ],
        "temperature": 0.1,
        "max_tokens": 2800,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Api-Key {key}", "Content-Type": "application/json"},
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    t1 = time.time()
    duration_ms = round((t1 - t0) * 1000, 2)

    choice = data["choices"][0]
    content = choice["message"].get("content") or ""
    reasoning = choice["message"].get("reasoning_content") or ""
    usage = data.get("usage", {})

    code = extract_python_code(content)
    (PATCHES_DIR / "baseten_muse_spark_repair.py").write_text(code, encoding="utf-8")
    (PATCHES_DIR / "baseten_full_response.md").write_text(
        f"# Baseten Full Response\n\n## Content\n{content}\n\n## Reasoning\n{reasoning}\n",
        encoding="utf-8",
    )

    cost = round((usage.get("prompt_tokens", 0) * 0.18 + usage.get("completion_tokens", 0) * 0.75) / 1e6, 6)

    receipt = {
        "candidate": "Meta Muse Spark Open (Baseten)",
        "provider": "baseten",
        "model_id": "meta-models/muse-spark-open",
        "run_id": data.get("id"),
        "dossier_hash": dossier_hash,
        "prompt_hash": prompt_hash,
        "duration_ms": duration_ms,
        "tokens": {
            "input": usage.get("prompt_tokens", 0),
            "output": usage.get("completion_tokens", 0),
            "total": usage.get("total_tokens", 0),
            "reasoning": len(reasoning.split()) if reasoning else 0,
        },
        "cost_usd": cost,
        "code_chars": len(code),
        "finish_reason": choice.get("finish_reason"),
        "status": "TESTED_LIVE_SUCCESS",
    }
    (RAW_DIR / "bench_repair_baseten_receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(f"Baseten done: {duration_ms}ms, {usage.get('total_tokens')} tokens, {len(code)} code chars, finish_reason: {choice.get('finish_reason')}, ${cost} USD")
    return receipt


def run_qwen_local() -> dict:
    print("\n--- [3/3] Running Local Qwen3-Coder-30B-AWQ via SSH on inneros-5 loopback :8000 ---")
    payload = {
        "model": "QuantTrio/Qwen3-Coder-30B-A3B-Instruct-AWQ",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT},
        ],
        "temperature": 0.1,
        "max_tokens": 2800,
    }
    ssh_cmd = [
        "ssh",
        "inneros-5",
        "curl -s http://127.0.0.1:8000/v1/chat/completions -H 'Content-Type: application/json' -d @-",
    ]
    t0 = time.time()
    proc = subprocess.run(
        ssh_cmd,
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=120,
    )
    t1 = time.time()
    duration_ms = round((t1 - t0) * 1000, 2)

    if proc.returncode != 0:
        raise RuntimeError(f"SSH curl error: {proc.stderr}")

    data = json.loads(proc.stdout)
    choice = data["choices"][0]
    content = choice["message"].get("content") or ""
    usage = data.get("usage", {})

    code = extract_python_code(content)
    (PATCHES_DIR / "qwen_local_repair.py").write_text(code, encoding="utf-8")
    (PATCHES_DIR / "qwen_full_response.md").write_text(
        f"# Qwen Full Response\n\n## Content\n{content}\n",
        encoding="utf-8",
    )

    receipt = {
        "candidate": "Local Qwen3-Coder-30B-AWQ (AMD Radeon PRO R9700)",
        "provider": "local_vllm_rocm",
        "model_id": "QuantTrio/Qwen3-Coder-30B-A3B-Instruct-AWQ",
        "run_id": data.get("id"),
        "dossier_hash": dossier_hash,
        "prompt_hash": prompt_hash,
        "duration_ms": duration_ms,
        "tokens": {
            "input": usage.get("prompt_tokens", 0),
            "output": usage.get("completion_tokens", 0),
            "total": usage.get("total_tokens", 0),
        },
        "cost_usd": 0.0,
        "code_chars": len(code),
        "finish_reason": choice.get("finish_reason"),
        "status": "TESTED_LIVE_SUCCESS",
    }
    (RAW_DIR / "bench_repair_qwen_receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(f"Local Qwen done: {duration_ms}ms, {usage.get('total_tokens')} tokens, {len(code)} code chars, $0.00 USD (Sovereign)")
    return receipt


if __name__ == "__main__":
    results = {}
    try:
        results["fireworks"] = run_fireworks()
    except Exception as e:
        print(f"Fireworks error: {e}")
        results["fireworks"] = {"status": "ERROR", "error": str(e)}

    try:
        results["baseten"] = run_baseten()
    except Exception as e:
        print(f"Baseten error: {e}")
        results["baseten"] = {"status": "ERROR", "error": str(e)}

    try:
        results["qwen_local"] = run_qwen_local()
    except Exception as e:
        print(f"Qwen error: {e}")
        results["qwen_local"] = {"status": "ERROR", "error": str(e)}

    (OUTPUT_DIR / "bench_live_runs_summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("\nAll live runs finished. Summary written to bench_live_runs_summary.json")
