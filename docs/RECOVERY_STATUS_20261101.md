# Code recovery and migration status | 2026-11-01

The standalone private Meta hackathon repository was initialized independently by Antigravity. This baseline was subsequently recovered from the old public composition branch in READ-ONLY mode. The old repository `main` was not modified, and the new repository has its own independent commit ancestry.

**Verification:** source recovered and locally tested: 16 standard-library unit tests passed after the paid Meta path was removed from the synthetic browser demo. The later ChatGPT session reportedly had 60 passing tests, but that entire workspace was not available during this transfer; DO NOT claim that those 60 tests exist in this git revision.

**Included:** synthetic incident simulator, deterministic/local Ollama inference, virtual actuator and readback, SQLite hash-chain evidence, offline tests, CI.

**NOT included / NOT_RUN:** live Guardian read connector, Personal Brain/Cognee verified recall connector, Meta Muse Spark 1.3 with one-shot credit authorization, SAM 3.1 lab image, integration of HA approvals/VoiceOps in this app, judge-facing hosted demo, contest video and submission. None of these may be presented as implemented simply because the existing commercial InnerOS platform has them.

Sources to reuse without rebuilding:
- Existing real Guardian service and read-only API: `Rafa-Innerchispa/inneros-nebius-nvidia-physical-ai-2026`; `https://guardian.creatorcore.ai/api/guardian/live/readings/{site}/{category}`.
- Existing verified memory `Rafa-Innerchispa/inneros-personal-brain` has loopback-only internal recall; do NOT expose the endpoint.
- AG-60 memory is in `Rafa-Innerchispa/innerops-agentic-platform`.
- Existing Home Assistant and VoiceOps authorization flows remain independent.
- Meta credits US$150 were requested, not confirmed. No new paid API call is authorized by this README.

Next: implement read-only integration and one-shot Meta operator flow with source-bound sanitized snapshots; capture real API receipts only after credit verification and explicit authorization. Build a protected judge site, video, and submit by 2026-11-04 21:00 Ecuador.
