# Evidence Report: Verified Meta Model API Second Live Run (Two-Server Redundant Topology)

**Date:** 2026-11-02 16:09 Ecuador / 21:09 UTC  
**Project:** InnerOS Autonomous Infrastructure Guardian & InnerOS Shared Model Provider  
**Operator:** Antigravity (Authorized by Rafael López, CEO of InnerChispa LLC)  
**Execution Grant ID:** `meta_grant_372c5433399c46bf3ecd4de7dd882800`  
**Authentic Provider Response ID:** `resp_6ae8fbeddf744fdb040c4cfd`  
**Truth Status:** `SYNTHETIC_LAB`  
**Provider Status:** `INCOMPLETE_MODEL_RESPONSE`  

---

## 1. Executive Summary

Following explicit owner authorization from Rafael López, we dispatched a single, live, non-replaying inference request to the official Meta Responses API (`https://api.meta.ai/v1/responses`).

- **Scenario:** Synthetic dual-server redundant infrastructure (SRV-A primary, SRV-B standby, 10G optical / 1G copper links, intermittent heartbeat, 0 customer or private PII).
- **HTTP Result:** `200 OK`.
- **Latency:** `5120.646 ms`.
- **Reasoning Effort:** `medium`.
- **Budget:** `max_output_tokens: 512`.
- **Actual Tokens Used:** 209 input, 512 output (510 reasoning tokens), 721 total tokens.
- **Completion Outcome:** The model utilized 510 tokens on its internal chain-of-thought, exhausting the 512-token budget before outputting visible completion text (`error_type: max_output_tokens`).
- **Fail-Closed Governance:** As mandated, the system classified the result as `INCOMPLETE_MODEL_RESPONSE`, recorded the receipt in the central ledger on `inneros-5-lan`, and halted immediately without retries or loops.

---

## 2. Complete Forensic Telemetry & Measurements

| Measurement | Value | Verification |
|:---|:---|:---|
| **HTTP Status Code** | `200 OK` | Authentic response from `api.meta.ai` |
| **Model** | `muse-spark-1.3` | Pinned reasoning model |
| **Provider Response ID** | `resp_6ae8fbeddf744fdb040c4cfd` | Authentic Meta provider ID |
| **Input Tokens** | `209` | Two-server synthetic scenario prompt |
| **Output Tokens** | `512` | Reached max output token budget |
| **Reasoning Tokens** | `510` | Internal Muse Spark reasoning effort (`medium`) |
| **Total Tokens** | `721` | Exact provider reported usage |
| **Observed Latency** | `5120.646 ms` | Network roundtrip & decode |
| **Request SHA-256** | `319c03af7bf25e1497f63e5b2a48c1279a2a9a03ecf25be68c46ab68a06cdb1b` | Cryptographic request digest |
| **Response SHA-256** | `6255fd9f015e0029ff4d56bfdfd7e8617e2a33a4c2be47ccfa3a89d21639dff2` | Cryptographic response digest |
| **Provider Completion Status** | `incomplete` (`max_output_tokens`) | 510 reasoning tokens out of 512 limit |
| **Automatic Retries** | `0` | Strict zero-replay policy |
| **Central Ledger Reconciliation** | `CONFIRMED` | Recorded in `model-provider-meta.sqlite3` |

---

## 3. Technical Analysis & Next Steps for Reasoning Model Budgets

Meta Muse Spark 1.3 includes internal reasoning tokens inside `max_output_tokens`. In this second trial:
- At `reasoning_effort: medium`, internal reasoning consumed **510 tokens**.
- Therefore, to obtain complete visible text output along with reasoning:
  1. `max_output_tokens` should be configured to **1024** (the ceiling we added in Phase A).
  2. `reasoning_effort` can be configured to `"low"` or remain `"medium"` with the full 1024 token budget.

The central ledger now documents:
- Total calls: 2
- Total tokens: 1,021 (300 + 721)
- Verified cost: $0.00 invented
