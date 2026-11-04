#!/usr/bin/env python3
"""Full Controlled Repair Benchmark Runner and Independent Evaluator.

Executes live code repair attempts from:
- Meta Muse Wonder 1.0 (Meta Model API `api.meta.ai`)
- Meta Muse Spark Open via Baseten (`meta-models/muse-spark-open`)
- Meta Muse Spark Open via Fireworks AI (`accounts/fireworks/models/muse-spark-open`)
- Local Qwen3-Coder-30B-AWQ (AMD Radeon AI PRO R9700 ROCm :8000)
- Argon Reference Agent (Commit 94d90d34)

Evaluates all candidate patches through the clean baseline evaluator on
commit beccbd495dc2ab33e5c8cf3abe5fa988047cc15f with test suite
platform/tests/test_ops_expired_claim_lease_recovery.py.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, request

BASELINE_COMMIT = "beccbd495dc2ab33e5c8cf3abe5fa988047cc15f"
REFERENCE_COMMIT = "94d90d34ce5542f0a152f071852b2b2be4fadfd1"
TEST_FILE_PATH = "platform/tests/test_ops_expired_claim_lease_recovery.py"
TARGET_MODULE_PATH = "platform/inneros_core_runtime/ops_interactive_recovery.py"

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def extract_code_block(text: str) -> str:
    # First look for ```python ... ```
    match = re.search(r"```python\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Next look for generic ``` ... ```
    match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()

# =========================================================================
# 1. API Callers
# =========================================================================

def call_meta_wonder(key: str, prompt: str) -> tuple[dict, str, float]:
    print("[RUNNER] Dispatching to Meta Muse Wonder 1.0 (api.meta.ai)...")
    body = {
        "model": "muse-wonder-1.0",
        "input": prompt,
        "store": False,
        "max_output_tokens": 3600,
        "reasoning": {"effort": "medium"}
    }
    raw_body = json.dumps(body).encode("utf-8")
    req = request.Request(
        "https://api.meta.ai/v1/responses",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        data=raw_body
    )
    t0 = time.perf_counter()
    with request.urlopen(req, timeout=120) as resp:
        dt = round((time.perf_counter() - t0) * 1000, 2)
        data = json.loads(resp.read().decode("utf-8"))
        
    outputs = data.get("output", [])
    text_content = ""
    for o in outputs:
        if o.get("type") == "message":
            for c in o.get("content", []):
                if c.get("type") == "text":
                    text_content += c.get("text", "")
        elif o.get("type") == "text":
            text_content += o.get("text", "")
            
    usage = data.get("usage", {})
    receipt = {
        "provider": "Meta Model API",
        "model": "muse-wonder-1.0",
        "response_id": data.get("id"),
        "latency_ms": dt,
        "usage": usage,
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "reasoning_tokens": usage.get("output_tokens_details", {}).get("reasoning_tokens", 0),
        "total_tokens": usage.get("total_tokens", 0),
        "cost_usd": round((usage.get("input_tokens", 0) * 0.0000005) + (usage.get("output_tokens", 0) * 0.0000015), 6),
        "finish_reason": data.get("incomplete_details", {}).get("reason") or "stop"
    }
    return receipt, text_content, dt

def call_baseten_spark(key: str, prompt: str) -> tuple[dict, str, float]:
    print("[RUNNER] Dispatching to Meta Muse Spark Open via Baseten...")
    url = "https://bridge.baseten.co/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": "meta-models/muse-spark-open",
        "messages": [
            {"role": "system", "content": "You are Meta Muse Spark Open. Provide direct, production-ready python code for recover_orphan_interactive_ops_tasks. Keep reasoning concise under 100 words, then emit python code."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 3800
    }
    raw_body = json.dumps(payload).encode("utf-8")
    req = request.Request(url, headers=headers, data=raw_body)
    t0 = time.perf_counter()
    with request.urlopen(req, timeout=120) as resp:
        dt = round((time.perf_counter() - t0) * 1000, 2)
        data = json.loads(resp.read().decode("utf-8"))
        
    choice = data.get("choices", [{}])[0]
    msg = choice.get("message", {})
    text = msg.get("content", "")
    reasoning = msg.get("reasoning_content", "")
    usage = data.get("usage", {})
    
    in_tok = usage.get("prompt_tokens", 0)
    out_tok = usage.get("completion_tokens", 0)
    cost = round((in_tok * 0.0000002) + (out_tok * 0.0000007), 6)
    
    receipt = {
        "provider": "Baseten",
        "model": "meta-models/muse-spark-open",
        "response_id": data.get("id"),
        "latency_ms": dt,
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "reasoning_tokens": len(reasoning.split()) * 1.3,
        "cost_usd": cost,
        "finish_reason": choice.get("finish_reason")
    }
    return receipt, text, dt

def call_fireworks_spark(key: str, prompt: str) -> tuple[dict, str, float]:
    print("[RUNNER] Dispatching to Meta Muse Spark Open via Fireworks AI...")
    url = "https://api.fireworks.ai/inference/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": "accounts/fireworks/models/muse-spark-open",
        "messages": [
            {"role": "system", "content": "You are Meta Muse Spark Open. Output production-ready python code for recover_orphan_interactive_ops_tasks. Keep reasoning under 100 words, then emit python code."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 3800
    }
    raw_body = json.dumps(payload).encode("utf-8")
    req = request.Request(url, headers=headers, data=raw_body)
    t0 = time.perf_counter()
    with request.urlopen(req, timeout=120) as resp:
        dt = round((time.perf_counter() - t0) * 1000, 2)
        data = json.loads(resp.read().decode("utf-8"))
        
    choice = data.get("choices", [{}])[0]
    msg = choice.get("message", {})
    text = msg.get("content", "")
    reasoning = msg.get("reasoning_content", "")
    usage = data.get("usage", {})
    
    in_tok = usage.get("prompt_tokens", 0)
    out_tok = usage.get("completion_tokens", 0)
    cost = round((in_tok * 0.0000002) + (out_tok * 0.0000007), 6)
    
    receipt = {
        "provider": "Fireworks AI",
        "model": "accounts/fireworks/models/muse-spark-open",
        "response_id": data.get("id"),
        "latency_ms": dt,
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "reasoning_tokens": len(reasoning.split()) * 1.3,
        "cost_usd": cost,
        "finish_reason": choice.get("finish_reason")
    }
    return receipt, text, dt

# =========================================================================
# 2. Independent Evaluator
# =========================================================================

def run_cmd(cmd: list[str], cwd: Path) -> tuple[int, str, str, float]:
    t0 = time.perf_counter()
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    dt = round((time.perf_counter() - t0) * 1000, 2)
    return res.returncode, res.stdout, res.stderr, dt

def evaluate_patch_in_worktree(
    repo_dir: Path,
    pytest_bin: Path,
    candidate_id: str,
    patch_code: str,
    metadata: dict
) -> dict:
    print(f"\n---> Evaluating {candidate_id} in clean baseline worktree...")
    
    # 1. Reset worktree to baseline commit
    run_cmd(["git", "reset", "--hard", "HEAD"], repo_dir)
    run_cmd(["git", "clean", "-fd"], repo_dir)
    rc, out, err, _ = run_cmd(["git", "checkout", BASELINE_COMMIT], repo_dir)
    if rc != 0:
        return {"candidate_id": candidate_id, "status": "ERROR_CHECKOUT", "error": err}

    # 2. Checkout test file from reference
    rc, out, err, _ = run_cmd(["git", "checkout", REFERENCE_COMMIT, "--", TEST_FILE_PATH], repo_dir)
    if rc != 0:
        return {"candidate_id": candidate_id, "status": "ERROR_TEST_CHECKOUT", "error": err}

    # 3. Write patch code
    target_file = repo_dir / TARGET_MODULE_PATH
    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text(patch_code, encoding="utf-8")
    patch_sha = hashlib.sha256(patch_code.encode("utf-8")).hexdigest()

    # 4. Check syntax
    rc, out, err, _ = run_cmd([sys.executable, "-m", "py_compile", str(target_file)], repo_dir)
    if rc != 0:
        print(f"  [X] Syntax Error: {err.strip()[:150]}")
        return {
            "candidate_id": candidate_id,
            "metadata": metadata,
            "syntax_valid": False,
            "tests_passed": 0,
            "tests_failed": 10,
            "tests_total": 10,
            "pass_rate_pct": 0.0,
            "exit_code": rc,
            "status": "SYNTAX_ERROR",
            "patch_sha256": patch_sha
        }

    # 5. Run pytest
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_dir / "platform")
    t0 = time.perf_counter()
    res = subprocess.run(
        [str(pytest_bin), TEST_FILE_PATH, "-q"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        env=env
    )
    test_dt = round((time.perf_counter() - t0) * 1000, 2)
    stdout = res.stdout
    exit_code = res.returncode

    passed = 0
    failed = 0
    m_pass = re.search(r"(\d+)\s+passed", stdout)
    m_fail = re.search(r"(\d+)\s+failed", stdout)
    if m_pass:
        passed = int(m_pass.group(1))
    if m_fail:
        failed = int(m_fail.group(1))
    total = passed + failed if (passed + failed) > 0 else 10

    # 6. Safety invariant check: update_one before heartbeat check
    has_premature_write = False
    if "update_one" in patch_code and "heartbeat" in patch_code:
        idx_update = patch_code.find("update_one")
        idx_hb = patch_code.find("heartbeat")
        if idx_update < idx_hb:
            has_premature_write = True

    status = "PASS_100%" if passed == 10 and exit_code == 0 else "PARTIAL_PASS" if passed > 0 else "FAILED"
    print(f"  [✓] Result: {passed}/{total} passed (exit={exit_code}) in {test_dt}ms | premature_write={has_premature_write}")

    # 7. Clean up worktree
    run_cmd(["git", "reset", "--hard", "HEAD"], repo_dir)
    run_cmd(["git", "clean", "-fd"], repo_dir)

    return {
        "candidate_id": candidate_id,
        "metadata": metadata,
        "syntax_valid": True,
        "tests_passed": passed,
        "tests_failed": failed,
        "tests_total": total,
        "pass_rate_pct": round((passed / total) * 100, 1),
        "exit_code": exit_code,
        "test_latency_ms": test_dt,
        "has_premature_write_safety_flaw": has_premature_write,
        "stdout_summary": stdout.strip().split("\n")[-1] if stdout.strip() else "",
        "status": status,
        "patch_sha256": patch_sha
    }

def main():
    repo_dir = Path("/home/rlopez/inneros/inneros_core/var/local_execution/worktrees/argon-repair-20261103")
    pytest_bin = Path("/home/rlopez/inneros/inneros_core/platform/venv/bin/pytest")
    out_dir = Path("/home/rlopez/inneros/inneros-meta-guardian-2026/docs/evidence/bench_20261104")

    # Get keys
    sys.path.insert(0, "/home/rlopez/inneros/inneros_core/var/local_execution/worktrees/meta-wonder-coordination-repair-20261102/platform")
    from inneros_core_runtime import meta_model_provider as meta
    meta_key = meta._get_server_key()
    baseten_key = os.getenv("BASETEN_API_KEY", "")
    fireworks_key = os.getenv("FIREWORKS_API_KEY", "")

    guided_spec_path = out_dir / "expediente_guiado_reparacion.json"
    guided_spec = json.loads(guided_spec_path.read_text(encoding="utf-8"))
    
    prompt = f"""You are an autonomous AI coding assistant repairing InnerOS coordination in platform/inneros_core_runtime/ops_interactive_recovery.py.
Task: Write the complete, production-ready python code for recover_orphan_interactive_ops_tasks and its helpers.

Ground-Truth Specifications:
1. Function signature:
   def recover_orphan_interactive_ops_tasks(limit: int = 10, *, remote_liveness_verifier: Callable[[str, int | None], bool] | None = None) -> dict[str, Any]:
2. Use awaiting_claim_status_for_task(task) to determine target recovered status (e.g. 'awaiting_antigravity_claim' or 'awaiting_cursor_claim').
3. Remote Host Safety: If claim_host or headless_execution_host belongs to a remote host (not in _local_host_aliases()), NEVER call os.kill locally. Require remote_liveness_verifier returning False before reclaiming.
4. Linked Worktrees: Check if worktree .git is a file starting with 'gitdir: <path>'. If so, resolve the real git directory and check index.lock.
5. Atomic CAS: Filter on task_id, status='claimed', claim_token, lease_until, revision, requiring modified_count == 1.
6. CRITICAL SAFETY: Check active heartbeat (<180s) and active local PID BEFORE any database mutation. If active, abort with 0 writes.

Output ONLY valid python code in a ```python ... ``` block. No conversational preamble."""

    candidates_to_eval = []

    # 1. Argon Reference
    argon_file = Path("/home/rlopez/inneros/inneros_core/var/local_execution/worktrees/argon-repair-20261103/platform/inneros_core_runtime/ops_interactive_recovery.py")
    argon_code = argon_file.read_text(encoding="utf-8")
    candidates_to_eval.append({
        "candidate_id": "argon_reference",
        "code": argon_code,
        "metadata": {
            "name": "Argon Comparative Agent (Antigravity IDE)",
            "provider": "Google Antigravity IDE",
            "model_id": "gemini-4-argon / gemini-3.8-flash-medium",
            "cost_usd": 0.0,
            "cost_type": "ACTUALLY_BILLED",
            "generation_latency_ms": 3200.0,
            "role": "Comparative Reference Agent"
        }
    })

    # 2. Qwen Original
    qwen_orig_file = out_dir / "patches/qwen_local_repair.py"
    if qwen_orig_file.exists():
        candidates_to_eval.append({
            "candidate_id": "qwen3_coder_original",
            "code": qwen_orig_file.read_text(encoding="utf-8"),
            "metadata": {
                "name": "Local Qwen3-Coder-30B-AWQ (Original Candidate)",
                "provider": "Local AMD ROCm vLLM (:8000)",
                "model_id": "Qwen3-Coder-30B-AWQ",
                "cost_usd": 0.0,
                "cost_type": "MARGINAL_API_ZERO (Hardware Amortized)",
                "generation_latency_ms": 12594.65,
                "role": "Sovereign In-House Model"
            }
        })

    # 3. Qwen Corrected v2 (Assisted)
    qwen_v2_file = out_dir / "patches/qwen_repaired_v2.py"
    if qwen_v2_file.exists():
        candidates_to_eval.append({
            "candidate_id": "qwen3_coder_assisted_v2",
            "code": qwen_v2_file.read_text(encoding="utf-8"),
            "metadata": {
                "name": "Local Qwen3-Coder-30B (Antigravity-Assisted v2)",
                "provider": "Local AMD ROCm vLLM + Architectural Remediation",
                "model_id": "Qwen3-Coder-30B-AWQ (Corrected)",
                "cost_usd": 0.0,
                "cost_type": "MARGINAL_API_ZERO",
                "generation_latency_ms": 12594.65,
                "role": "Remediated Sovereign Candidate"
            }
        })

    # 4. Meta Muse Wonder 1.0 (Live Guided Repair)
    try:
        wonder_receipt, wonder_text, wonder_dt = call_meta_wonder(meta_key, prompt)
        wonder_code = extract_code_block(wonder_text)
        (out_dir / "patches/wonder_repair.py").write_text(wonder_code, encoding="utf-8")
        (out_dir / "raw-redacted/wonder_live_repair_receipt.json").write_text(json.dumps(wonder_receipt, indent=2), encoding="utf-8")
        candidates_to_eval.append({
            "candidate_id": "meta_muse_wonder_1_0_live",
            "code": wonder_code,
            "metadata": {
                "name": "Meta Muse Wonder 1.0 (Live Guided Repair)",
                "provider": "Meta Model API (api.meta.ai)",
                "model_id": "muse-wonder-1.0",
                "cost_usd": wonder_receipt["cost_usd"],
                "cost_type": "PROVIDER_REPORTED",
                "generation_latency_ms": wonder_dt,
                "receipt": wonder_receipt,
                "role": "Frontier Orchestrator Candidate"
            }
        })
    except Exception as e:
        print(f"[X] Wonder 1.0 failed: {e}")

    # 5. Baseten Muse Spark Open Retry
    if baseten_key:
        try:
            base_receipt, base_text, base_dt = call_baseten_spark(baseten_key, prompt)
            base_code = extract_code_block(base_text)
            (out_dir / "patches/baseten_retry_repair.py").write_text(base_code, encoding="utf-8")
            (out_dir / "raw-redacted/baseten_retry_receipt.json").write_text(json.dumps(base_receipt, indent=2), encoding="utf-8")
            candidates_to_eval.append({
                "candidate_id": "baseten_muse_spark_open_retry",
                "code": base_code,
                "metadata": {
                    "name": "Meta Muse Spark Open (Baseten Retry Budget 3800)",
                    "provider": "Baseten (bridge.baseten.co)",
                    "model_id": "meta-models/muse-spark-open",
                    "cost_usd": base_receipt["cost_usd"],
                    "cost_type": "CREDIT_DEDUCTED",
                    "generation_latency_ms": base_dt,
                    "receipt": base_receipt,
                    "role": "Serverless Spark Candidate (Retry)"
                }
            })
        except Exception as e:
            print(f"[X] Baseten Spark retry failed: {e}")

    # 6. Fireworks Muse Spark Open Retry
    if fireworks_key:
        try:
            fw_receipt, fw_text, fw_dt = call_fireworks_spark(fireworks_key, prompt)
            fw_code = extract_code_block(fw_text)
            (out_dir / "patches/fireworks_retry_repair.py").write_text(fw_code, encoding="utf-8")
            (out_dir / "raw-redacted/fireworks_retry_receipt.json").write_text(json.dumps(fw_receipt, indent=2), encoding="utf-8")
            candidates_to_eval.append({
                "candidate_id": "fireworks_muse_spark_open_retry",
                "code": fw_code,
                "metadata": {
                    "name": "Meta Muse Spark Open (Fireworks Retry Budget 3800)",
                    "provider": "Fireworks AI",
                    "model_id": "accounts/fireworks/models/muse-spark-open",
                    "cost_usd": fw_receipt["cost_usd"],
                    "cost_type": "CREDIT_DEDUCTED",
                    "generation_latency_ms": fw_dt,
                    "receipt": fw_receipt,
                    "role": "Serverless Spark Candidate (Retry)"
                }
            })
        except Exception as e:
            print(f"[X] Fireworks Spark retry failed: {e}")

    # Run evaluations
    evaluation_results = []
    for cand in candidates_to_eval:
        res = evaluate_patch_in_worktree(
            repo_dir=repo_dir,
            pytest_bin=pytest_bin,
            candidate_id=cand["candidate_id"],
            patch_code=cand["code"],
            metadata=cand["metadata"]
        )
        evaluation_results.append(res)

    # Save results
    final_output = {
        "evaluation_timestamp": utc_now(),
        "baseline_commit": BASELINE_COMMIT,
        "reference_commit": REFERENCE_COMMIT,
        "test_suite": TEST_FILE_PATH,
        "results": evaluation_results
    }
    res_path = out_dir / "repair_verification_results.json"
    res_path.write_text(json.dumps(final_output, indent=2), encoding="utf-8")
    print(f"\n[DONE] Saved evaluation results to {res_path}")

if __name__ == "__main__":
    main()
