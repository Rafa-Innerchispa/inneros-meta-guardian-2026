# Evidence Report: Verified Meta Model API First Live Run (No-Card Verification)

**Date:** 2026-11-01  
**Project:** InnerOS Autonomous Infrastructure Guardian & InnerOS Resource Fabric  
**Operator:** Antigravity (Pair Programming with Rafael López, CEO of InnerChispa LLC)  
**Execution Probe ID:** `meta-no-card-20261101`  
**Authentic Provider Response ID:** `resp_6ae763441da65bb847084f88`  
**Meta Request ID:** `b3e2109e-b56d-44de-b08a-c6d6c965dfe3`  

---

## 1. Executive Summary

We executed the authorized first single-request live probe of the Meta Model API to answer the critical question:
> **Does the Meta Model API function using the promotional $150 credit balance without an active credit card registered?**

**Finding:** **YES.** The Meta API returned `HTTP 200 OK` (not `HTTP 402 Payment Required`). The key was successfully authenticated, and the request was processed by `muse-spark-1.3`.

---

## 2. Complete Forensic Telemetry & Measurements

All private artifacts were captured with strict redaction of credentials:
- Claim file: `runtime/meta_trials/meta-no-card-20261101/claim.json`
- Request file: `runtime/meta_trials/meta-no-card-20261101/request.json`
- Provider response: `runtime/meta_trials/meta-no-card-20261101/provider_response.json`
- Private receipt: `runtime/meta_trials/meta-no-card-20261101/receipt.json`

| Measurement | Value | Verification |
|:---|:---|:---|
| **HTTP Status Code** | `200 OK` | Authentic response from `api.meta.ai` |
| **Model** | `muse-spark-1.3` | Pinned reasoning model |
| **Provider Response ID** | `resp_6ae763441da65bb847084f88` | Authentic provider completion ID |
| **Meta Request ID** | `b3e2109e-b56d-44de-b08a-c6d6c965dfe3` | `x-request-id` header |
| **Input Tokens** | `108` | Synthetic test prompt |
| **Output Tokens** | `192` | Reached max output token budget |
| **Reasoning Tokens** | `190` | Internal Muse Spark reasoning effort |
| **Total Tokens** | `300` | Exact billed usage |
| **Observed Latency** | `3273.322 ms` | Network roundtrip & decode |
| **End-to-End Throughput** | `58.656 tokens/sec` | Verified performance |
| **Request SHA-256** | `ef01a9f81e8d3fd71d3dfdddb3da85de592691384c10389cd27dc06b39dc1142` | Cryptographic request digest |
| **Response SHA-256** | `c096408b1635262c05c434c706bc01a43488a12b0dae7d4fa7c2af709ab8093e` | Cryptographic response digest |
| **Response Payload Size** | `1160 bytes` | Cleaned JSON |
| **Provider Status** | `incomplete` (`max_output_tokens`) | Reasoning effort consumed 190 of 192 tokens |

---

## 3. Technical Finding: Reasoning Model Token Sizing

`muse-spark-1.3` is an agentic reasoning model that operates with high reasoning effort by default. In this probe, `max_output_tokens` was capped at `192`. The model used `190` tokens exclusively on internal reasoning steps, hitting the token limit before generating visible output text. 

**Recommendation for production usage:** Future authorized requests should provide `max_output_tokens >= 512` so the model has room for both its reasoning chain and visible completion text.

---

## 4. Central Resource Fabric & Vault Integration

The Meta Model API has been established as a shared, reusable provider in the core platform:

- **Repository:** `https://github.com/Rafa-Innerchispa/innerops-agentic-platform`
- **Canonical Vault Reference:** `owner_vault:model_api_provider/meta_model_api_key`
- **Funding Registry:**
  - Program: `Meta Global AI Developer Hackathon 2026`
  - Credit Account: `Meta Model API Promotional Credits ($150)` (`meta-model-api`)
  - Linked Consumer Project: `inneros-meta-guardian-2026`
- **Capabilities Registered:**
  - `model.provider.query.v1` (Read-only: status, health, comparison, project usage)
  - `model.frontier.reason.v1` (Mutation: governed one-shot grant issuance and execution)
- **Home Assistant Owner Approval Verification:**
  - Strict verification function `verify_ha_owner_approval` enforces owner actor `RAFAEL`, matching prompt SHA-256, unexpired TTL, and token budget ceiling before dispatch.
  - Local AMD Ryzen AI vLLM remains the primary default engine (0 USD cost, airgapped LAN privacy). Meta is invoked only when explicitly authorized for frontier reasoning.
