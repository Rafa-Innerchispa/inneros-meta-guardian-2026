# Meta Muse Wonder — InnerOS Coordination Incident Package (evidence-first)
**Created:** 2026-11-02 19:52 Ecuador / 2026-11-03 00:52 UTC.
**Project:** InnerOS Autonomous Infrastructure Guardian · Meta x Cerebral Valley.
**State:** READY_FOR_LOCAL_ANALYSIS; MUSE_WONDER_NOT_RUN; NO_VERIFIED_SELF_HEAL.
**Executor:** ChatGPT coordinating a **separate** case study. Antigravity is committed to other development. DO NOT dispatch or reclaim its work.

## Scope of the experiment
Can a specialist reasoning model help the local AMD Qwen system find reproducible root causes of InnerOS agent-coordination incidents, propose bounded code repairs, and achieve independently verified improvement without reusing old grants, looping paid agents, exposing private state or modifying production?

The goal is not simply the four failed tests. Analyze the **end-to-end agent lifecycle**: request -> classification -> deduplication -> owner authorization -> claim/lease -> local or approved external executor -> evidence -> verification -> completion -> notification. Distinguish incorrect test assertions from real production faults.

## Source A: Live coordination snapshot
Source: InnerOS MCP `get_coordination_live()`, revision **48660**, time **2026-11-03T00:52:33.725103Z**.
These are *ledger projections*, not physical process counts or causes.

| State | Records |
|---|---:|
| All open coordination records | **175** |
| Pending human review | **102** |
| Blocked | **61** |
| Queued | **11** |
| Claimed | **1** |
| Blocker: stale_ops_task_timeout | **41** |
| Blocker: worker_not_started | **7** |
| Blocker: worker_not_started_scheduler_dispatch_missed | **3** |
| Another blocker: product task contract/path policy | **1** |

The one `claimed` record has a stored lease expired **2026-10-19T17:07:09Z** and has not been updated since **2026-10-19T16:07:09Z**. A stale ledger projection is not evidence that its executor is running or spending.
The separate Dev Swarm scheduler status at this snapshot reports **enabled=true, active_worker_count=0**. Zero workers can mean no eligible authorized work; prove a specific eligible task was skipped before alleging scheduler malfunction.

Change from snapshot revision 48567 (2026-11-02 21:07 UTC): open records **172 -> 175**, blocked **61 -> 61**, queued **11 -> 11**, claimed **1 -> 1**, pending review **99 -> 102**. This is a descriptive before/before trend, not an after-repair comparison.

## Source B: Real CI failure baseline
GitHub Actions run: https://github.com/Rafa-Innerchispa/innerops-agentic-platform/actions/runs/41510104055
Recorded: **333 passed, 4 failed, 13 subtests passed**.
Four categories (not yet validated as implementation defects):
1. `test_local_model_router_fallback::test_failed_fallback_remains_fail_closed` — status-contract mismatch for failed AMD/Intel local routing.
2. `test_ops_auto_claim_admission::test_manual_tasks_are_never_auto_claimed` — manual/automation admission gate.
3. `test_ops_antigravity_false_completion_regression::test_antigravity_headless_script_declares_bounded_executor_plan` — false-completion / bounded execution evidence contract.
4. `test_provider_execution_trust_boundary::test_codex_real_path_blocked_without_grant_and_env` — external provider owner-grant trust boundary.

Earlier isolated local Muse metrology tests: 23/23 passed; they prove instrumentation, not a repaired coordination system. Some targeted local tests imported host code outside the worktree and are not hermetic proof.

## Source C: Historical architecture analysis, not current runtime proof
Notion decision/document dated 2026-10-31: https://app.notion.com/p/40acb2deeb0f8177a8abda7d3ec0e3d5
- Coordination uses MongoDB, Temporal, local Dev Swarm and HA approvals; no end-to-end automatic closure verified.
- Intel deployment was documented; AMD parity and consistent fleet limits were outstanding.
- Duplicated headless/systemd spawning and credit exhaustion were identified as risks.
- Inbox messages, task queue, approval records and actual executor runs are separate systems; a message or ACK is **not** execution.
- The historical document proposed a single task contract, fleet-wide paid-concurrency governor and explicit completed-verification gate.
- These are historical findings/proposals, not proof all conditions remain active in November.

## Source D: Security boundary outstanding
Code security draft: https://github.com/Rafa-Innerchispa/innerops-agentic-platform/pull/252
State at package creation: **OPEN DRAFT; NOT MERGED OR DEPLOYED**. Tests on the draft do not certify production authentication.
Known concerns included legacy owner HMAC scope, Companion receipt verification with absent secret, reusing approval to mint grants, and untrusted receipt reconciliation. A draft security patch must be reviewed and tested with the real approval producer.

## Source E: Meta real model receipts
Previous **Muse Spark 1.3**, NOT Muse Wonder:
- First documented probe: incomplete, 108 input + 192 output = 300 tokens; no useful visible diagnosis.
- Second documented probe: incomplete, 209 input + 512 output = 721 tokens, 510 hidden reasoning tokens, approximately 5.121 sec; no visible diagnosis, no automatic retries reported.
Evidence: https://github.com/Rafa-Innerchispa/inneros-meta-guardian-2026/blob/main/docs/evidence/META_SECOND_RUN_VERIFIED_20261102.md
Central MCP provider query previously returned **0 receipts** while an operator report says 2 calls on another host. Provenance and actual Meta billing still require independent reconciliation. Do not claim a verified amount billed or a live Wonder result.

## Safe experimental data boundary
Present **aggregated counts, isolated test names, exact CI URLs, causal hypotheses and specifically owner-approved excerpts**. Do NOT upload raw MongoDB task rows, site names, private agent conversations, customer data, host IP/MAC addresses, logs with tokens, secrets, billing data, or unrestricted repository source. Meta's first single call must remain a synthetic/sanitized reproduction until a signed separate data-release gate exists.

## Read-only research questions for AMD/Qwen, then Wonder
1. Which exact producer, admission transition or reconciliation function could leave a task claimed after lease expiry? What proves it?
2. Why do 41 tasks carry `stale_ops_task_timeout` and 10 worker-start blockers? Are they historical terminal records, active retry candidates, or stuck live tasks?
3. Are `pending_human_review` tasks correctly waiting for owner or a missing notification/approval? What evidence distinguishes these cases?
4. Is task classification incorrectly converting routine email/research messages into coding tasks requiring a repo/worktree?
5. Could a job be marked COMPLETED without repo modification, correct test target, strong executor receipt and independent verification?
6. Where can idempotency/one-use approval be duplicated across Mongo, Temporal, local workers and external IDEs?
7. Which narrow patches or tests can prove causal improvement without a deployment or spending credits?

## Model output contract
Answer must return for every hypothesis:
- severity, confidence, exact source evidence and what is **unknown**;
- actual owner/producer/consumer code path to inspect;
- minimal code patch (proposed, not executed);
- negative regression test and positive control;
- expected before/after metric and how to independently verify;
- change scope, rollback, privacy/authorization risks.
Prioritize no paid agent loop, no false completion, no duplicate claims, no silent approval and no irreversible host writes.

## Execution gates
1. LOCAL AMD Qwen first; record actual model version, latency, GPU/RAM/energy if available, tokens if observed; label NOT_RUN otherwise.
2. One **new owner-verified** Muse Wonder 1.0 diagnostic grant, if/when security and account terms are verified; preflight budget <= US$0.50, max 4096 output tokens, **0 automatic retries**, no tools, no uncontrolled subprocesses; no implicit authorization from these notes.
3. Review model suggestions. Apply selected patch in isolated worktree only, with approval. Rerun identical targeted and broader regressions from reproducible environment.
4. Declare VERIFIED_HEAL only if independent before/after evidence shows a repaired function and no new security regressions. Otherwise mark PARTIAL, BLOCKED or NOT_RUN.

**This document is a measured experiment input, not Antigravity's undisclosed latest personal IDE summary. That separate summary was not located in the shared inboxes, Notion or GitHub at creation time.**
