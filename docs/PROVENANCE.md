# Provenance, Prior Work & Hackathon Attribution Disclosure
**Project:** InnerOS Autonomous Infrastructure Guardian  
**Hackathon:** Meta Global AI Developer Hackathon 2026 (Startup Track / Push the Frontier)  
**Date:** November 1, 2026  

---

## 1. Pre-existing Work (Disclosed & Credited)

InnerChispa LLC maintains an ongoing operational ecosystem. We explicitly disclose the following pre-existing components:

* `Rafa-Innerchispa/inneros-physical-guardian`: Permanent product containing RTSP/ONVIF ingestion, telemetry collectors, and device interfaces developed prior to the Meta event.
* `Rafa-Innerchispa/inneros-nebius-nvidia-physical-ai-2026` & `https://guardian.creatorcore.ai/`: Production deployment providing read-only REST readings for physical infrastructure (`GET /api/guardian/live/readings/{site}/{category}`) across Casa and Bellini sites.
* `Rafa-Innerchispa/innerops-agentic-platform`: Network engineer operational memory schema (`network_engineer_memory.py`) in MongoDB.
* `Rafa-Innerchispa/inneros-voiceops-one-day-2026`: Telephone operational verification engine (Asterisk PBX, Piper TTS, Whisper STT) including the historical call proof from October 30, 2026.
* Existing InnerOS host infrastructure (Intel 1.4, AMD 1.5 with ROCm vLLM).

---

## 2. Meta Event-Specific Implementations (Built Oct 26 – Nov 1, 2026)

This repository (`Rafa-Innerchispa/inneros-meta-guardian-2026`) is a **completely independent, dedicated codebase** with its own Git history, tests, and deployment artifacts. The following components were authored specifically for this hackathon:

1. **Meta Muse Spark 1.3 One-Shot Operator (`meta_once.py`)**:
   - Official Responses API integration (`POST https://api.meta.ai/v1/responses`, model `muse-spark-1.3`).
   - Single-use cryptographic grant validation with atomic pre-dispatch consumption to strictly prevent replay attacks or infinite retry loops.
   - Deep regex-based privacy redaction stripping all private IPs, MAC addresses, and credentials from prompts.
   - Structured four-part output parser: Observations, Hypotheses, Uncertainty, and Governed Recommended Action.
   - Safe `NOT_RUN` receipt with deterministic local fallback when API key is unconfigured or credits pending.
2. **Meta SAM 3.1 Visual Lab Inspector (`sam_inspector.py`)**:
   - Optical inspection component analyzing physical laboratory rack hardware (SFP transceivers, fiber bend radius compliance) using authorized bench assets with zero customer PII.
3. **Live Infrastructure Adapter (`integrations.py`)**:
   - Normalized connector consuming live telemetry feeds from Casa and Bellini sites, extracting freshness and SHA-256 snapshot digests.
4. **Verified Memory Client (`integrations.py`)**:
   - Curated historical site baseline and topology facts with strict PII and credential scrubbing.
5. **Governed 7-Stage Engine (`engine.py`)**:
   - Unified operational loop: `OBSERVE ➔ REMEMBER ➔ REASON ➔ AUTHORIZE ➔ ACT ➔ VERIFY ➔ PROVE`.
6. **Tamper-Evident SHA-256 Audit Chain (`evidence.py`)**:
   - Sequential cryptographic hash chaining linking every state transition from observation through readback verification.
7. **Comprehensive Test Suite (40 Automated Tests)**:
   - 40 unit and integration tests covering the complete state machine, one-shot grants, replay prevention, privacy redaction, and web API contracts. Runs 100% offline in CI without paid credentials.
8. **Modern Judge Web Console (`index.html`, `app.js`, `styles.css`)**:
   - Responsive dark interface for desktop and mobile, with live ingestion buttons, grant management, and forensic JSON evidence export.

---

## 3. Truth Boundary & Safety Guarantees

* Live infrastructure telemetry is strictly **read-only**.
* Virtual actuators operate within process isolation; no arbitrary device actuation occurs over the web console.
* Model-generated text never has authority to execute actions; only the human owner (Rafael López) can authorize state progression.
* Every piece of telemetry and evidence carries an explicit, honest truth label: `LIVE_INFRASTRUCTURE_READING`, `VERIFIED_HISTORICAL_MEMORY`, `GOVERNED_ONE_SHOT_RECEIPT`, `SIMULATED_FIXTURE`, or `HISTORIC_RECORDED_VOICEOPS_CALL`.
