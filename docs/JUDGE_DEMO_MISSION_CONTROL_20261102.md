# InnerOS × Meta Muse Wonder | Judge Demo Runbook (authoritative, 2026-11-02)
**Owner:** InnerChispa LLC. **Track:** Meta Global AI Developer Hackathon, Startup Track.
**Deadline:** 2026-11-04 21:00 Ecuador, per competition project handoff. Verify portal confirmation separately.
**Audience:** Technical judges. **Duration:** target 2:40–2:55.
**Release:** Demo PR only. No production deployment or live paid model calls.

## Narrative: two layers, one self-preserving infrastructure system
The core idea is *a guardian for physical infrastructure that can also investigate the agents guarding it*. Present TWO linked capabilities, not a random set of unrelated AI API screenshots:

**Layer A — Physical Guardian, existing functional console at /**:
- Ingest an explicitly labeled synthetic sensor incident OR read-only live network data (only if the configured API is reachable and source freshness verified).
- Show the OBSERVE → REMEMBER → REASON → APPROVE → ACT → VERIFY → PROVE sequence.
- The local deterministic path works offline. The live telemetry adapter may be unavailable; do not claim it is live if not connected.
- Only an in-process virtual actuator runs from the public web, not actual door/gate/camera control.
- SAM 3.1 panel is a STATIC FIXTURE, NOT a SAM model call; VoiceOps evidence is HISTORICAL, not a new call.

**Layer B — Agent Self-Healing Mission Control, new functional console at /self-heal**:
- Show original four failing coordination contracts from GitHub Actions.
- Show the historical central MCP snapshot (179 open tasks, 41 stale timeout, 0 workers recorded) **as a dated snapshot**, not live polling.
- Compare the operator-reported Muse Wonder 1.0 response (3,442 tokens, 22.06s, claimed HTTP 200) to independently passing 339/339 core candidate-branch CI.
- Disclose that local AMD/Qwen comparison is NOT_MEASURED for this exact case, Meta billing and owner approval provenance are still unverified, and the response was to sanitized fictional data, not raw production logs.
- Run the interactive *in-memory deterministic lab*: inject synthetic stale claim → local rule-based analysis → replay Wonder receipt reference → sandbox operator acknowledgement → virtual patch → independent invariant readback → export hash-chained JSON.
- Keep paid endpoints disabled and no fake owner approvals. This is a **demonstration of the governance flow**, NOT a live agent repairing production.

## Video script in English (use actual captured screen, no synthetic voice claims)
**0:00–0:20** — Face camera or rack: "In critical facilities, cameras and networks aren't the only things that fail. The AI agents managing them can also get stuck, duplicate work, or claim success without evidence. We built InnerOS to protect infrastructure, including its own control plane."

**0:20–0:42** — Existing Physical Guardian tab: "Here is the infrastructure side. We can ingest read-only network signals where available, or clearly labeled test incidents. Every action passes through owner governance, and our public demonstration uses only virtual actuation."

**0:42–1:05** — Self-Healing Mission Control hero and original failure cards: "Then we found four coordination regression failures in our own agent platform. We did not hide those failures. We preserved the original CI run and treated them as a measurable incident."

**1:05–1:35** — Model side-by-side: "InnerOS is local-first. Our AMD/Qwen stack is the intended first investigator. To study a harder case, we also tested Meta Muse Wonder 1.0 through the Meta Model API. The server-side report records 3,442 tokens and 22 seconds. This was a sanitized case. We disclose what has and hasn't been independently verified."

**1:35–2:12** — Replay lab, click actions in order (not too fast): "This is the governed repair loop in a safe sandbox. Observe the expired claim, diagnose, replay the historical Wonder recommendation, acknowledge a sandbox repair, apply a virtual patch, and independently verify the final state. No autonomous model can authorize itself or spend in this web UI."

**2:12–2:38** — CI before/after and audit JSON: "The most important number comes from actual code CI: a previous run showed four failures; our clean candidate branch reached 339 of 339 passing tests. Some corrections affect code, others repair test contracts. We haven't deployed this to production, and we don't pretend otherwise."

**2:38–2:52** — Face camera or title screen: "InnerOS is designed to observe, reason, ask permission, act safely, verify and prove. The future isn't more agents. It's agents you can trust when something goes wrong."

## Working local screen/demo start
From this private hackathon repository, with Python 3.10+:
~~~
PYTHONPATH=src python -m inneros_meta_guardian.web
~~~
Open **http://127.0.0.1:8787/** for the Physical Guardian, then **http://127.0.0.1:8787/self-heal** for the new lab. The server binds to localhost by default; the unauthenticated demo must NOT be exposed directly on a public network.

All demo tests (no paid calls):
~~~
PYTHONPATH=src python -m unittest discover -s tests -v
node --check src/inneros_meta_guardian/static/self-heal.js
~~~

## Evidence & source of truth
- Original core CI: https://github.com/Rafa-Innerchispa/innerops-agentic-platform/actions/runs/41558176002
- Candidate core CI: https://github.com/Rafa-Innerchispa/innerops-agentic-platform/actions/runs/41569825744
- Clean candidate code review: https://github.com/Rafa-Innerchispa/innerops-agentic-platform/pull/253
- Approval hardening: https://github.com/Rafa-Innerchispa/innerops-agentic-platform/pull/252
- Wonder operator report: https://github.com/Rafa-Innerchispa/inneros-meta-guardian-2026/blob/main/docs/evidence/MUSE_WONDER_SELF_HEALING_VERIFIED_20261102.md
- Independent limitations review: https://github.com/Rafa-Innerchispa/inneros-meta-guardian-2026/blob/main/docs/evidence/INDEPENDENT_REVIEW_WONDER_RUN_AND_CLEAN_PORT_20261102.md

## Hard truth gates, before filming/submitting
- Never show the lab simulator as a *live Wonder inference*, *live Qwen*, or *production repair*.
- Do not say the self-heal is deployed or merged; code PR #253 remains separate until independently approved.
- Do not say the 49/49 operator trial means the **four original CI failures** were all fixed: the fourth suite differs.
- Do not call Meta billing "verified" without independent provider statement; costs quoted are estimates.
- Record the official submission ID/confirmation from Cerebral Valley. A README checkbox is not proof of submission.
- The private repo is not automatically visible to judges; provide an accessible video and any requested share permissions.
