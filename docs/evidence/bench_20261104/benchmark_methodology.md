# Controlled Repair Benchmark Methodology
## InnerOS Autonomous Infrastructure Guardian × Meta Ecosystem
**Task:** `ops_2f5f7283d70b` | **Baseline Commit:** `beccbd495dc2ab33e5c8cf3abe5fa988047cc15f`  
**Dossier SHA-256:** `18498ec83b3ec86a50a5b6e953b94f59b05e12a39f1552aa3eae023ec5190d90`  
**Cutoff:** November 4, 2026, 21:00 Ecuador

---

## 1. Ground Truth Incident & Baseline Defect

The benchmark evaluates autonomous diagnosis and code repair on an authentic distributed coordination failure in the InnerOS agentic platform:
- **Baseline Git Commit:** `beccbd495dc2ab33e5c8cf3abe5fa988047cc15f`
- **Target File:** `platform/inneros_core_runtime/ops_interactive_recovery.py`
- **Test Suite:** `platform/tests/test_ops_expired_claim_lease_recovery.py`
- **Baseline Status:** **9 FAILED, 1 PASSED in 0.15s**

### The 5 Core Invariants:
1. **DEFECT_01 (Precedence):** Orchestrated tasks must preserve `awaiting_antigravity_claim` or `awaiting_cursor_claim` instead of generic `awaiting_ide_claim`.
2. **DEFECT_02 (Cross-Host PID Hazard):** Calling `os.kill(pid, 0)` is strictly invalid when `claim_host != socket.gethostname()`. Remote hosts (Intel `ralphi-ia-ver-10`) must not be evaluated with local PID checks unless a `remote_liveness_verifier` is explicitly supplied; otherwise they must be safely skipped with `remote_host_unverified:<host>`.
3. **DEFECT_03 (Worktree .git Pointer File):** Linked git worktrees contain a `.git` text file (`gitdir: <path>`) rather than a directory. Recovery must parse `gitdir:` to inspect `<path>/index.lock`. If locked, recovery must skip the task with `worktree_git_locked`.
4. **DEFECT_04 (Atomic CAS):** Database updates in recovery must enforce multi-field Compare-And-Swap matching `task_id`, `status`, `claim_token`, `lease_until`, and `revision`, requiring `modified_count == 1`.
5. **DEFECT_05 (Heartbeat & PID Liveness Guard):** Tasks with active local PIDs or recent heartbeats (< 180s) must never be recovered even if `lease_until` is in the past.

---

## 2. Experimental Controls & Fairness

To guarantee an unbiased, scientifically reproducible comparison:
1. **Identical Canonical Dossier:** Every candidate model receives the exact same incident dossier (`expediente_canonico_reparacion.json`, SHA-256 `18498ec8...`).
2. **Zero Pre-Conditioning:** No model is provided prior solutions, prior test files, or Argon's historical patch.
3. **Worktree Isolation:** Every repair attempt runs in an isolated worktree branch without cross-contaminating other models or production `main`.
4. **Independent Sandbox Verification:** Modal Cloud CPU sandbox is utilized strictly as an execution sandbox, not as a language model.
5. **Financial & Cost Controls:** Zero unapproved spend, single-use approval grants, zero automatic retries on paid endpoints.

---

## 3. Evaluation Criteria

Each candidate is evaluated across six rigorous dimensions:
1. **Diagnostic Accuracy:** Number of ground-truth defects correctly identified in reasoning traces.
2. **Code Repair Correctness:** Number of unit tests passed in `test_ops_expired_claim_lease_recovery.py` (out of 10).
3. **Regression Safety:** Zero regressions introduced into previously working behavior.
4. **Interface Contract Adherence:** Preserves existing module signatures and backward compatibility.
5. **Latency & Throughput:** Time-to-first-token, inference duration, and end-to-end execution time.
6. **Operational Cost:** Micro-spend incurred per query and per verified patch.
