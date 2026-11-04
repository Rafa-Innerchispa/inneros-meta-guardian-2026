# InnerOS Autonomous Infrastructure Guardian
**The Infrastructure That Investigates and Heals Itself**  
*Meta Global AI Developer Hackathon 2026 — Startup Track (Push the Frontier / Build for Your World)*  
InnerChispa LLC · Guayaquil, Ecuador · Rafael López, Founder & CEO

[![Public Demo](https://img.shields.io/badge/Live%20Demo-https%3A%2F%2Fguardian.pcdoctor.ai%2Fself--heal-success?style=for-the-badge&logo=cloudflare)](https://guardian.pcdoctor.ai/self-heal)
[![Unit Tests](https://img.shields.io/badge/tests-87%2F87%20passing-brightgreen?style=for-the-badge)](https://github.com/Rafa-Innerchispa/inneros-meta-guardian-2026)
[![Python 3.10 | 3.12](https://img.shields.io/badge/python-3.10%20%7C%203.12-blue?style=for-the-badge)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)

---

## Verified Public Demonstration

> 🌐 **PUBLIC HTTPS URL:** **[https://guardian.pcdoctor.ai/self-heal](https://guardian.pcdoctor.ai/self-heal)**  
> **Mode:** `PUBLIC_JUDGE_DEMO` (Cloudflare Tunnel TLS 1.3, origin isolated, fail-closed read-only gate, 0 unapproved model spend, zero VPN required).  
> **Access:** Direct public inspection (safe read-only mode, mutations strictly blocked with HTTP 403).  
> **Deployment Architecture:** Documented in [`docs/JUDGE_PUBLIC_DEPLOY.md`](docs/JUDGE_PUBLIC_DEPLOY.md).

---

## Overview

Most AI systems today answer questions inside chat windows. **InnerOS Autonomous Infrastructure Guardian** investigates and repairs its own multi-agent coordination layer and physical facility sensors using local-first sovereign models and governed Meta frontier capabilities:

```text
OBSERVE (Context Collector) ➔ INVESTIGATE (Tool Loop: Local Qwen 30B / Meta Muse Wonder 1.0) ➔ GOVERN (Policy & Single-Use Grant) ➔ REPAIR ARENA (Isolated Worktrees: Muse Code vs. Argon) ➔ VERIFY (Independent CI & Readback) ➔ PROVE (SHA-256 Audit Chain)
```

- **Forensic Diagnosis:** Grounded in a real coordination failure (`InnerOS Global Snapshot`, SHA-256 `92796a03...`) with 15-day expired task claims, cross-host PID kill hazards, and linked worktree `.git` lock misses.
- **Provider Lab & Financial Controls:** Verified ledger across Fireworks AI ($20.30 available, auto-reload OFF), Baseten ($5.00 Model APIs + $2.00 Tool Calls), Modal ($1.00 CPU Sandbox, $29 card offer denied), and Meta Model API (10-day evaluation window).
- **Independent Benchmark Arena:** Evaluates agents side-by-side on identical baseline commit `beccbd49` with 9/10 failing tests without cross-contamination.
- **Unified Ten-Domain Audit Dossier:** Comprehensive cluster audit covering AMD & Intel topology, MCP Small/Monolithic routing, queue leases, worktree locks, and deterministic repair invariants.

---

## Multi-Model Benchmark & Independent Audit

Evaluated under strict local-first governance (zero unapproved spend, single-use grants, no auto-merge to `main`):

| Evaluation Criteria | Meta Muse Wonder 1.0 / Code 1.4 | Argon Comparative Agent (Antigravity) | GPT-6 Astra (OpenAI) | Local Sovereign Baseline (Qwen 30B AWQ) |
|---|---|---|---|---|
| **Diagnostic Mode** | Authentic 2-turn tool loop (`resp_6aea9747...` $\rightarrow$ 4 tool calls $\rightarrow$ `resp_6aea97f2...`) | Antigravity IDE comparative session | Evaluated: `BLOCKED_API_ACCESS` (Missing API credits) | Sovereign on-premises vLLM `:8000` (ROCm 10.1) |
| **Diagnostic Latency** | `25,816.73 ms` (`3,843` tokens, **`822` reasoning CoT**) | `3,200 ms` (`1,950` tokens) | N/A (Blocked at auth frontier) | **`6,440.31 ms`** (`1,522` tokens) |
| **Repair Worktree** | `var/local_execution/worktrees/meta-muse-code-repair-20261103` | `var/local_execution/worktrees/argon-repair-20261103` | N/A | Local verification suite |
| **Code Repair Commit** | Stopped safely at auth gate | Commit [`94d90d34`](https://github.com/Rafa-Innerchispa/innerops-agentic-platform/commit/94d90d34ce5542f0a152f071852b2b2be4fadfd1) (+537, -14 lines) | N/A | Baseline PR #256 |
| **Verification Tests** | 40 MSP events logged (`docs/evidence/muse_repair_session_events.jsonl`) | **10 / 10 Tests Passed (100% Green in 0.13s)** | 0 attempted | 43/43 targeted tests passing |
| **Cost Incurred** | **`$0.00 USD`** (Governed single-use grant) | **`$0.00 USD`** | **`$0.00 USD`** | **`$0.00 USD`** (Private GPU) |
| **Integrity Status** | **`BLOCKED_AT_AUTH_BOUNDARY`** (Truthfully reported) | **`VERIFIED_PASS`** | **`BLOCKED_API_ACCESS`** (No silent fallback) | **`ONLINE_SOVEREIGN`** |

---

## 8 Interactive Mission Control Panels (`/self-heal`)

1. **Autonomous Diagnostic Orchestrator (5 Panels):** Direct diagnostic chat connected to `inneros_global_snapshot.json` and 11 allowlisted read-only and simulation tools (`get_pending_tasks`, `get_worker_health`, `read_source_file`, etc.).
2. **Provider Lab & Financial Controls:** Real-time ledger tracking balances ($26.30 external available, $0.00 unapproved spend), zero-spend dry-run contracts, and per-call budget ceilings.
3. **Unified Ten-Domain Audit Dossier:** Comprehensive audit table inspecting cluster topology, MCP Small (:8001) vs Monolithic (:8102), worker queues, and deterministic repair invariants.
4. **Meta Model Lab:** Central registry of 11 components with measured single/2-turn latencies, context limits, token pricing, hardware limitations, and single-use owner approval tokens.
5. **Agent Repair Arena:** Side-by-side comparative repair duel with diff statistics, test verdicts, and rollback integrity.
6. **Forensic Evidence Explorer:** Direct links to authentic receipts, CI runs, and commit diffs.
7. **Interactive Replay Sandbox:** 6-stage in-memory state machine demonstrating safe approval order (observe $\rightarrow$ local $\rightarrow$ wonder $\rightarrow$ ack $\rightarrow$ patch $\rightarrow$ verify).
8. **Physical Guardian (`/`):** SAM 3.1 optical switch LED segmentation, Grandstream VoiceOps telephone verification, and tamper-evident SHA-256 hash chains.

---

## Quickstart & Verification

```bash
# 1. Run the Complete Test Suite (87 Tests, 100% Offline Passing)
PYTHONPATH=src python -m unittest discover -s tests -v

# 2. Run the Security & Secret Sanitization Check (0 leaks guaranteed)
python scripts/build_public_release.py --check

# 3. Launch Local Operator Server (Port 8787)
PYTHONPATH=src python -m inneros_meta_guardian.web
```

---

## Evidence Index

- [`docs/evidence/meta_wonder_tool_investigation_20261103.json`](docs/evidence/meta_wonder_tool_investigation_20261103.json): Authentic 2-turn tool-calling investigation receipt from **Meta Muse Wonder 1.0**.
- [`docs/evidence/fireworks_live_receipt_20261104.json`](docs/evidence/fireworks_live_receipt_20261104.json): Authentic live API completion receipt from **Fireworks AI** (`muse-spark-open`, $0.000317 USD).
- [`docs/evidence/baseten_live_receipt_20261104.json`](docs/evidence/baseten_live_receipt_20261104.json): Authentic live API completion receipt from **Baseten** (`muse-spark-open`, $0.000271 USD).
- [`docs/evidence/modal_live_receipt_20261104.json`](docs/evidence/modal_live_receipt_20261104.json): Authentic isolated ephemeral container execution receipt from **Modal** ($0.000039 USD).
- [`docs/evidence/repair_benchmark_comparison_20261103.json`](docs/evidence/repair_benchmark_comparison_20261103.json): Independent repair evaluation (Argon 10/10 vs. Muse Code vs. Astra vs. Qwen).
- [`docs/evidence/inneros_unified_audit_dossier_20261104.json`](docs/evidence/inneros_unified_audit_dossier_20261104.json): Complete ten-domain cluster audit and multi-model findings.
- [`docs/evidence/inneros_unified_audit_dossier_20261104.md`](docs/evidence/inneros_unified_audit_dossier_20261104.md): Human-readable markdown audit dossier.
- [`docs/SUBMISSION_PACKAGE_20261104.md`](docs/SUBMISSION_PACKAGE_20261104.md): Cerebral Valley submission fields, 3-minute video script, and HeyGen avatar prompt.
