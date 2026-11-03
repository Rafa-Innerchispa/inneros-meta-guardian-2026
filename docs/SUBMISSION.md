# Meta Global AI Developer Hackathon 2026 — Submission package
**Project:** InnerOS Autonomous Infrastructure Guardian
**Tagline:** The Infrastructure That Remembers and Responds
**Track:** Startup · Push the Frontier / Build for Your World
**Owner:** InnerChispa LLC (Guayaquil, Ecuador)
**Deadline:** Wednesday, November 4, 2026 at 21:00 Ecuador time (9:00 PM ET)
**Portal:** https://cerebralvalley.ai/e/meta-ai-developer-hackathon
**Repo:** https://github.com/Rafa-Innerchispa/inneros-meta-guardian-2026 (PRIVATE; sharing may be needed)
**Status:** RUNNABLE LOCAL DEMO / SUBMISSION NOT CONFIRMED

## Judge-ready project description (English)

InnerOS is an autonomous infrastructure guardian designed for the physical systems that businesses rely on: networks, cameras, access controls and edge servers. It observes real read-only signals where connected, recalls prior context when available, proposes governed actions and records verifiable evidence.

We extended that idea to a less visible but serious risk: the AI agents managing infrastructure can themselves become stuck, duplicate work or report completion without proof. For Meta's hackathon, we used a real InnerOS coordination CI incident as a measurable case study. Our team tested Meta Muse Wonder 1.0 with a sanitized, fictional reproduction of four regression symptoms. The operator's trial report records a completed response with 3,442 tokens and about 22 seconds of latency. We then evaluated targeted code and test-contract corrections in isolated branches.

The independently verifiable result is a clean coordination candidate passing **339/339** GitHub CI tests, compared with a prior CI run showing four failures. The experiment demonstrates the engineering building blocks of governed self-repair, not an autonomous patch to live production. Our frontend gives judges two working experiences: a physical infrastructure Guardian and a safe, interactive self-healing replay with approval, virtual state repair, independent checks and a SHA-256 event chain.

Our long-term architecture is local-first: AMD/Qwen handles private context and routine diagnosis; Meta's frontier model is an explicitly authorized external specialist for difficult cases. No model may approve its own paid invocation or physical changes.

## What works and what does not (truth table)

| Capability | State | Meaning |
|---|---|---|
| Physical Guardian frontend at / | WORKING LOCAL WEB DEMO | Real read-only intake when configured, synthetic incidents otherwise |
| Self-Healing Mission Control at /self-heal | WORKING LOCAL WEB DEMO | Historical CI/Meta evidence and interactive deterministic sandbox |
| Guardian offline Python CI | VERIFIED | 69/69 tests on Python 3.10 and 3.12 |
| Coordination candidate PR #253 | VERIFIED IN GITHUB CI | 339/339 passing, 13 extra subtests; not merged or deployed |
| Muse Wonder 1.0 provider response | OPERATOR-REPORTED | HTTP 200 completed, 3442 tokens, 22.06 sec according to redacted receipt |
| Wonder provider billing & exact signed approval | NOT RECONCILED | Do not present estimated charges as verified billing |
| Four original production defects fixed | NOT VERIFIED | Two source changes and two test-contract changes; no live worker state recheck |
| Home Assistant approval hardening | DRAFT | PR #252; pending producer migration and end-to-end notification checks |
| Wonder through InnerOS MCP | DRAFT | Stacked PR #254; current active MCP still defaults to Spark |
| Comparable Qwen analysis of exact case | NOT MEASURED | Target architecture, not a fabricated benchmark |
| SAM 3.1 optical view | STATIC FIXTURE | No actual SAM 3.1 model call is claimed |
| Cognee memory | CONDITIONALLY UNAVAILABLE | Fail closed if service cannot prove memory facts |
| Public live demo deployment | NOT CONFIRMED | App binds to loopback; no unauthenticated public hosting |
| Cerebral Valley submission | PENDING | Require the portal's explicit confirmation ID |

## Reproducible demonstration

Start from the repo with Python 3.10+:
~~~
PYTHONPATH=src python -m inneros_meta_guardian.web
~~~
- Open http://127.0.0.1:8787/ to show the Physical Guardian.
- Open http://127.0.0.1:8787/self-heal to show Muse self-healing incident.
- Click **Inject fixture → Local analysis → Replay Muse receipt → Lab acknowledge → Virtual repair → Independent readback**.
- Export the sandbox JSON with a hash-chained event history.
- Demonstrate the separately linked actual GitHub CI runs.
- Do not call Meta from the web or describe the synthetic lab as a real production repair.

Test:
~~~
PYTHONPATH=src python -m unittest discover -s tests -v
node --check src/inneros_meta_guardian/static/self-heal.js
~~~

## Evidence links
- Original CI, 4 failures: https://github.com/Rafa-Innerchispa/innerops-agentic-platform/actions/runs/41558176002
- Clean candidate CI, 339 passed: https://github.com/Rafa-Innerchispa/innerops-agentic-platform/actions/runs/41569825744
- Candidate code: https://github.com/Rafa-Innerchispa/innerops-agentic-platform/pull/253
- Governance / approval hardening: https://github.com/Rafa-Innerchispa/innerops-agentic-platform/pull/252
- Wonder MCP bridge: https://github.com/Rafa-Innerchispa/innerops-agentic-platform/pull/254
- Muse Wonder operator case: https://github.com/Rafa-Innerchispa/inneros-meta-guardian-2026/blob/main/docs/evidence/MUSE_WONDER_SELF_HEALING_VERIFIED_20261102.md
- Independent evidence limitations: https://github.com/Rafa-Innerchispa/inneros-meta-guardian-2026/blob/main/docs/evidence/INDEPENDENT_REVIEW_WONDER_RUN_AND_CLEAN_PORT_20261102.md
- Judge narration and screen sequence: [JUDGE_DEMO_MISSION_CONTROL_20261102.md](JUDGE_DEMO_MISSION_CONTROL_20261102.md)

## Final delivery checklist
- [x] Hackathon repository and original Physical Guardian console.
- [x] New Self-Healing Mission Control frontend and no-spend sandbox API.
- [x] Python 3.10 / 3.12 offline CI green, with JS syntax verification.
- [x] Original and after-PR CI proof URLs; short-lived code-review branch.
- [x] Redacted operator Wonder metrics and limitations disclosed.
- [x] English judge runbook with <3-minute target.
- [ ] Validate actual screen recordings and frontend appearance in a desktop browser.
- [ ] Confirm a judges-accessible delivery medium (demo video, public demo if securely hosted, or granted private repo access).
- [ ] Record/edit final demo video with actual screen capture. Do not imply a generated mock interface is the running app.
- [ ] Check exact fields and format in the authenticated Cerebral Valley submission form.
- [ ] Submit officially and preserve confirmation ID, timestamp and link.
- [ ] Production authorization/security PRs require separate approval; not hackathon submission prerequisites for the local demo.

**Safety:** The CLI/HTTP demo does not expose paid Muse calls, customer telemetry secrets or destructive actions. No public bind without a separate authentication and network security review. This document is a submission draft, not the portal submission receipt.
