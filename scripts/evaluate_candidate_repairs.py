#!/usr/bin/env python3
"""Independent Evaluator for Autonomous Code Repair Candidates.

Evaluates candidate repair patches against the common baseline commit
beccbd495dc2ab33e5c8cf3abe5fa988047cc15f and test suite
platform/tests/test_ops_expired_claim_lease_recovery.py.

Guarantees:
- Clean baseline checkout for each candidate
- Strict syntax verification (py_compile)
- Full pytest execution capturing stdout/stderr/exit code
- Invariant safety analysis (detecting pre-condition bypasses)
- Zero residual modifications to the worktree
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

BASELINE_COMMIT = "beccbd495dc2ab33e5c8cf3abe5fa988047cc15f"
REFERENCE_COMMIT = "94d90d34ce5542f0a152f071852b2b2be4fadfd1"
TEST_FILE_PATH = "platform/tests/test_ops_expired_claim_lease_recovery.py"
TARGET_MODULE_PATH = "platform/inneros_core_runtime/ops_interactive_recovery.py"

def sha256_file(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run_cmd(cmd: list[str], cwd: Path) -> tuple[int, str, str, float]:
    t0 = time.perf_counter()
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    dt = round((time.perf_counter() - t0) * 1000, 2)
    return res.returncode, res.stdout, res.stderr, dt

def evaluate_patch(
    repo_dir: Path,
    pytest_bin: Path,
    candidate_id: str,
    patch_code: str,
    candidate_metadata: dict
) -> dict:
    print(f"\n========================================================")
    print(f"Evaluating candidate: {candidate_id}")
    print(f"========================================================")

    # 1. Reset worktree to baseline commit
    run_cmd(["git", "reset", "--hard", "HEAD"], repo_dir)
    run_cmd(["git", "clean", "-fd"], repo_dir)
    rc, out, err, _ = run_cmd(["git", "checkout", BASELINE_COMMIT], repo_dir)
    if rc != 0:
        return {"candidate_id": candidate_id, "status": "ERROR_CHECKOUT", "error": err}

    # 2. Checkout the test file from reference
    rc, out, err, _ = run_cmd(["git", "checkout", REFERENCE_COMMIT, "--", TEST_FILE_PATH], repo_dir)
    if rc != 0:
        return {"candidate_id": candidate_id, "status": "ERROR_TEST_CHECKOUT", "error": err}

    # 3. Write candidate patch code
    target_file = repo_dir / TARGET_MODULE_PATH
    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text(patch_code, encoding="utf-8")
    patch_sha = hashlib.sha256(patch_code.encode("utf-8")).hexdigest()

    # 4. Check python syntax
    rc, out, err, comp_dt = run_cmd([sys.executable, "-m", "py_compile", str(target_file)], repo_dir)
    if rc != 0:
        print(f"Syntax error in candidate {candidate_id}: {err}")
        return {
            "candidate_id": candidate_id,
            "metadata": candidate_metadata,
            "syntax_valid": False,
            "tests_passed": 0,
            "tests_failed": 10,
            "tests_total": 10,
            "exit_code": rc,
            "stderr": err,
            "status": "SYNTAX_ERROR",
            "patch_sha256": patch_sha
        }

    # 5. Run pytest suite
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

    # 6. Parse pytest output
    stdout = res.stdout
    stderr = res.stderr
    exit_code = res.returncode

    passed = 0
    failed = 0
    import re
    # Match lines like "10 passed in 0.09s" or "9 failed, 1 passed in 0.17s"
    m_pass = re.search(r"(\d+)\s+passed", stdout)
    m_fail = re.search(r"(\d+)\s+failed", stdout)
    if m_pass:
        passed = int(m_pass.group(1))
    if m_fail:
        failed = int(m_fail.group(1))

    total = passed + failed if (passed + failed) > 0 else 10

    # 7. Check critical safety invariants
    # Invariant: check if patch contains premature update_one before heartbeat check
    has_premature_write = False
    if "update_one" in patch_code and "heartbeat" in patch_code:
        idx_update = patch_code.find("update_one")
        idx_hb = patch_code.find("heartbeat")
        if idx_update < idx_hb:
            has_premature_write = True

    status = "PASS_100%" if passed == 10 and exit_code == 0 else "PARTIAL_PASS" if passed > 0 else "FAILED"

    print(f"Result for {candidate_id}: {passed}/{total} passed, exit_code={exit_code}, latency={test_dt}ms")
    if has_premature_write:
        print(f"WARNING: Critical safety flaw detected: premature DB write before heartbeat check!")

    # 8. Clean worktree
    run_cmd(["git", "reset", "--hard", "HEAD"], repo_dir)
    run_cmd(["git", "clean", "-fd"], repo_dir)

    return {
        "candidate_id": candidate_id,
        "metadata": candidate_metadata,
        "syntax_valid": True,
        "tests_passed": passed,
        "tests_failed": failed,
        "tests_total": total,
        "pass_rate_pct": round((passed / total) * 100, 1) if total > 0 else 0.0,
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

    if not repo_dir.exists():
        print(f"Repo dir not found: {repo_dir}")
        sys.exit(1)

    print(f"Baseline commit: {BASELINE_COMMIT}")
    print(f"Test suite: {TEST_FILE_PATH}")
    print(f"Evaluator initialized successfully.")

if __name__ == "__main__":
    main()

