# InnerOS Self-Healing with Meta Muse Wonder 1.0
**Execution contract / continuation of original Meta x Cerebral Valley objective**
Date: 2026-11-02. Project: `inneros-meta-guardian-2026`. Owner: InnerChispa LLC.
Status: **MEASURED LOCAL BASELINE / WONDER NOT_RUN / NO VERIFIED HEAL**.

## Real objective, not merely an API demonstration
Connect Muse Wonder as an **external specialist in the existing local-first InnerOS coordination control plane**. InnerOS observes its own failures, diagnoses locally with AMD/Qwen first, escalates a constrained case to Wonder if unresolved, receives concrete root-cause hypotheses and suggested repairs, applies approved changes only in isolated worktrees, reruns tests and independent coordination checks, then records whether the repair actually worked. The 7-stage loop is OBSERVE -> REMEMBER -> REASON -> AUTHORIZE -> ACT -> VERIFY -> PROVE.

A single synthetic Wonder response is the safety/quality **first stage**, not the whole project. The desired second stage is an interactive coding agent able to inspect a **curated, owner-approved** slice of the failing source and sanitized run context, suggest a patch and use local tools under constraints. A third stage integrates this as a reusable capability surfaced to ChatGPT via InnerOS MCP.

## Latest grounded baseline (2026-11-02 at 21:07 UTC)
Source of current coordination counters: InnerOS MCP get_coordination_live(), revision **48567**. These are coordination ledger states, not independently verified active processes.
- Open ops records: **172**, consisting of **99 pending_human_review**, **61 blocked**, **11 queued**, **1 claimed**.
- **41** blocked records have `stale_ops_task_timeout`; **7** `worker_not_started`; **3** `worker_not_started_scheduler_dispatch_missed`.
- The single claimed record was last updated 2026-10-19 and its recorded lease is expired. Stale claiming must be independently checked, not automatically deleted.
- Scheduler separately reported **0 active workers** (2026-11-02).
- The central Meta MCP usage query for `inneros-meta-guardian-2026` returned **0 calls, 0 tokens, no receipts** at that instant. This is inconsistent with the historical **300-token incomplete** Muse Spark provider probe reportedly stored on another host; do not infer there was no historical call, reconcile and verify source/host first.
- Genuine independent GitHub Actions incident: https://github.com/Rafa-Innerchispa/innerops-agentic-platform/actions/runs/41510104055 : **333 passed / 4 failed / 13 subtests passed**. Four categories: local fallback status contract; manual task admission; Antigravity false-completion test; provider trust boundary. Failed assertions may reflect outdated expectations rather than unsafe behavior.
- On 2026-11-02 ChatGPT created an isolated local worktree in the existing allowlisted core repo and ran `python -m unittest discover -s platform/tests -p 'test_muse*.py' -v`: **23 tests PASS in 1.007s**. One targeted fallback suite still failed 1/4, and Antigravity false-completion targeted suite still failed at least 1 assertion. Caution: traceback imports showed shared host core modules outside the worktree, so these locally targeted results MUST NOT be presented as hermetic regression proof.
- From ChatGPT, the allowlisted local executor rejected `python -m inneros_core_runtime.muse_wonder_trial --dry-run ...` with `command_not_allowlisted`; **no network call and no Meta credit use occurred**. The local repo lock was released. The current `model.frontier.reason.v1` capability has no `model_id` selection and central provider hardcodes `muse-spark-1.3`. Therefore a **live Wonder interaction from ChatGPT through that capability is NOT available today**.

## Two independent access routes
**A. First-party local terminal coding agent:** Meta Muse Code (`muse` interactive; `muse exec` headless). It is optional and may require a local installation; confirm current actual model/usage before running. See https://dev.meta.ai/docs/muse-code .

**B. No new IDE:** Reuse a *separate* local Codex CLI environment (dedicated `CODEX_HOME`, not Rafael's existing default Codex config) with Model API as an OpenAI Responses provider: `base_url=https://api.meta.ai/v1`, `env_key=MODEL_API_KEY`, `model=muse-wonder-1.0`, `wire_api=responses`. Meta documents this at https://dev.meta.ai/docs/coding-agents . Secret must be injected only from the trusted InnerOS owner vault into the isolated process environment, never written to a repo, chat, stdout or reusable global profile. Codex is then **an agent runtime**, while the inference model is Meta Wonder; do not mistake this for consuming OpenAI Codex API credits.

**C. Directly from ChatGPT:** extend the existing `model.frontier.reason.v1` design into a new governed version supporting `muse-wonder-1.0`, OR expose a narrow one-shot `muse.wonder.trial.v1` capability through the existing MCP. Implementation must be deployed, discoverable and tested before claiming that this chat can invoke Wonder. No direct ChatGPT access to owner-vault secret. Never expose an anonymous model proxy.

## Security blockers to fix before real spending or execution
1. `verify_ha_owner_approval` in `platform/inneros_core_runtime/meta_model_provider.py` still accepts a legacy HMAC candidate lacking signed expiry/model; reject old signatures and require signed expiry, model, reasoning effort, scoped prompt digest, nonce and output cap with regression tests. Check the real HA Companion verifier uses the same binding.
2. `MetaGrantLedger.reconcile_receipt` accepts caller-supplied dictionaries and can record success based on unverified fields; prevent untrusted reconciliation, independently confirm receipt provenance and issuer, and restrict the reconciliation capability to a trusted operator. Do not claim Meta billed charges merely because SQLite shows a row.
3. Atomic consume a one-use owner grant before network, with expiry, fixed model, project, exact sanitized prompt SHA, effort, token cap and budget. No automatic retries. Distinguish authorizing a **single request** from authorizing a **multi-call coding agent**.
4. Data-release gate: no raw customer/site data, IPs, MACs, credentials, unpublished proprietary files, raw memory snapshots or unrestricted GitHub repository content sent to Meta by default. Start with a sanitized diagnostic bundle; only expand the approved source scope explicitly.
5. No main/production changes, site/device commands, credentials install, systemd restart or payment-method changes as part of model reasoning. Worktree patches require independent human or policy-gated approval and CI verification.

## Experiment sequence: measured and reproducible
1. **Observe**. Snapshot current coordination metrics, reference URLs/SHAs, exact reproduced test failures, state of 172 open ops, expired claim and 41 stale timeouts. Store safe evidence and source timestamps, not raw secrets.
2. **Local primary (A)**. AMD Qwen diagnoses the same case, record model SHA/version, device backend, input/output tokens where measured, wall/first-token latency, GPU/VRAM/energy if observable, hypothesized defects, patch proposal and uncertainty. Do not pretend a local run happened if not recorded.
3. **Wonder one-shot (B)**. Existing core `muse_wonder_trial.py` is a synthetic-only, no-tool probe. Run `--dry-run` on a **trusted local terminal**, then (after step 4 security clearance and owner one-use approval) a single `muse-wonder-1.0` Standard call with output limit 4096 and conservative budget `<= US$0.50`. Capture real response ID, status, visible content, input/cached/output/reasoning tokens, request/response digest, latency, estimate and provider-billed cost when independently available. If INCOMPLETE or blocked, retain the negative result and stop; do not silently retry.
4. **Interactive source-aware diagnosis (C)**. Only *after* a positive B review and a **separate**, limited budget authorization, run an isolated coding-agent session (prefer existing Codex CLI powered by Meta Model API, or Muse Code) with a sanitized, allowlisted source bundle and read-only tools first. Deny uncontrolled subagent fanout, external network tools, persistent background sessions and any unbounded iteration loop; implement server-side spend and request-count enforcement before enabling multi-turn. Model's 1M-token context is a capacity, not a reason to upload the whole private repo.
5. **Act**. Apply a selected patch on a disposable isolated worktree, inspect diff, approval and rollback plan. Keep runtime and customer infrastructure untouched.
6. **Verify**. Compare *same* four targeted CI tests before/after, plus security and integration regression suites, same code/commit provenance, then independently check coordination invariant changes (stale claiming, dedup, ACK and real work completion evidence).
7. **Prove**. Append event hashes to private journal, preserve separately anchored digest, publish only redacted judge-safe tables, screenshots, CI links, code SHAs and clearly qualified conclusions (NOT_RUN, BLOCKED, PARTIAL, CANDIDATE_PATCH, VERIFIED_HEAL). Record “cost per verified issue fixed” only if at least one issue was independently fixed.

## Minimal evidence and stage gates
Case ID `inneros-agent-coordination-p0`; baseline source CI run 41510104055; current coordination snapshot revision 48567.
A measurement row must include: run ID, model/provider and actual version, target SHA, branch, timestamp, prompt checksum, data classification, valid owner approval/ref, attempt/retry count, response ID, completion status, tokens (input/cached/output/reasoning), wall latency, time-to-first-token if streamed, estimate vs verified USD, candidate files/LOC, baseline/post tests and CI URLs, regressions, exact blocker, and human review time.

**Definition of success:** at least one real Meta Wonder COMPLETED response useful for this case; independently verified patch or scientifically useful negative result; transparent before/after measurements; no secret or unapproved spend exposure; safe official submission. A self-healing **claim** additionally requires a verified automatic detect->authorized local repair->independent recheck->auditable event sequence, not merely tests passing or a model describing a fix.

## Ownership and non-duplication
- Core: `Rafa-Innerchispa/innerops-agentic-platform`, owner vault, durable governance, patch execution and audit metrics.
- Competition presentation: `Rafa-Innerchispa/inneros-meta-guardian-2026`, demo/UI/evidence/submit; never copy Meta secret.
- Antigravity can complete the pending interactive IDE work referenced by existing inbox `msg_2becaf1ce87a9f2b`. Do not open a duplicate autolaunched DevSwarm/Temporal task, trigger Cursor loops or silently rerun the paid request.
- ChatGPT is the read-only evidence auditor and can start future *governed* capabilities only after they are actually deployed and have valid grants.

Official documentation: https://dev.meta.ai/docs/overview , https://dev.meta.ai/docs/coding-agents , https://dev.meta.ai/docs/pricing-rate-limits .
