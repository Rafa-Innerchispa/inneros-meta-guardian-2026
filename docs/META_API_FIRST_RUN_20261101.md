# Meta Model API first live probe | 2026-11-01

**Owner:** InnerChispa LLC. **Purpose:** Verify whether the US$150 promotional credits allow one Muse Spark 1.3 call WITHOUT adding a payment method.

This is a local terminal procedure, not a public web API. It uses fictional laboratory telemetry, never a client network, Home Assistant, cameras, billing card or VoiceOps.

## Ground truth
- Owner screenshot from Billing: Free credits in use $150.00, current balance $0.00, "Please add a payment method".
- Owner says an API key is created; key has NOT been tested.
- Official billing says payment method and business information are normally required even with promotional credits.
- No hard dollar cap is available; Meta Spend Limits only sends alerts.
- Meta warns submitted content under free credits may be used for product improvement; this script uses *fictional* input only.

Official references:
https://dev.meta.ai/docs/api-reference/responses/create-response
https://dev.meta.ai/docs/authentication
https://dev.meta.ai/help/billing/set-up-billing
https://dev.meta.ai/docs/error-handling
https://dev.meta.ai/help/billing/spend-limit-alert

## 1. Get current code and run tests

Pull latest main of https://github.com/Rafa-Innerchispa/inneros-meta-guardian-2026 and verify Python 3.10+.

Windows PowerShell:

    $env:PYTHONPATH="src"
    python -m unittest discover -s tests -q

Linux/macOS:

    PYTHONPATH=src python3 -m unittest discover -s tests -q

Do NOT execute scripts/make_one_shot_grant.py and scripts/operator_meta_once.py as two unrelated processes: the older grant store is not persistent. This new smoke probe is a separate, explicit ONE CALL diagnostic.

## 2. Provide the key privately, without pasting into chat or shell history

Prefer the authorized local secret vault. Otherwise, in an interactive Windows PowerShell terminal:

    $sec = Read-Host "Meta Model API key (local only)" -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
    try { $env:MODEL_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
    Remove-Variable sec,ptr

Or on Linux/macOS Bash (masked input):

    read -r -s -p "Meta API key: " MODEL_API_KEY
    echo
    export MODEL_API_KEY

Never paste the key into an agent prompt, a chat, source code, a GitHub issue, git commits, CI variables with public logs or screenshots.

## 3. Authenticate without generating

    python -m inneros_meta_guardian.meta_probe --check-key

Sends exactly one GET https://api.meta.ai/v1/models (no generation). Saves a private receipt under runtime/meta_trials/auth_*.json.

Possible status: AUTH_ENDPOINT_OK (key accepted, billing not proven); AUTH_FAILED/HTTP 401; BILLING_BLOCKED/HTTP 402; or NO_KEY.

## 4. Try exactly ONE real synthetic call

The owner authorized one cost-bounded trial. Run:

    python -m inneros_meta_guardian.meta_probe --one-shot --probe-id meta-no-card-20261101 --owner-authorized

Sends at most one POST https://api.meta.ai/v1/responses using:
- model muse-spark-1.3
- max_output_tokens 192 (reasoning + visible output)
- store false
- short fictional lab heartbeat prompt
- no tools, real telemetry, personal information or client devices
- timeout 12 seconds, ZERO automatic retries

Creates an exclusive local directory/claim BEFORE dispatch; the SAME probe ID cannot be reused even after timeout or 402.

Possible results: REAL_SUCCESS (HTTP 200 + completed + authentic provider ID + visible text), BILLING_BLOCKED (HTTP 402), KEY_REJECTED (401), PERMISSION_BLOCKED (403), HTTP_ERROR, NETWORK_ERROR, UNVERIFIED_RESPONSE.

**If HTTP 402 / billing_not_configured: STOP.** This directly establishes that Meta requires completing billing; only the owner may decide whether to register a payment method. DO NOT retry automatically.

## 5. Required private measurement artifacts

In runtime/meta_trials/meta-no-card-20261101/ :
- claim.json: one-request authorization and start timestamp
- request.json: exact synthetic request, hash and output cap
- provider_response.json: entire provider response/error if returned, scrubbed of API key
- receipt.json: status, actual HTTP code, provider response ID, output text, input/output/total tokens, request latency, request and response SHA-256, response bytes, safe request-id and rate-limit headers, approximate end-to-end tokens/second, source truth label

runtime/ is gitignored. Keep these records on the local protected workstation; publish only a redacted summary.

The provider-cost field is null until a real cost is reported by Meta. Compare Usage in Meta Billing after the request (it may take time to update); never invent a dollar cost or p95 performance from a single trial.

End the session by removing the key environment variable. PowerShell: Remove-Item Env:MODEL_API_KEY. Bash: unset MODEL_API_KEY.

## 6. Next milestone

If REAL_SUCCESS, attach the sanitized receipt in docs/evidence/ as a redacted summary, then do Guardian read-only + actual Personal Brain recall + approved Meta inference with minimum safe signal subset. Never claim full real-world E2E until every step is evidenced. Keep SAM clearly SIMULATED_FIXTURE until a real model call with a permitted lab image exists.

If BILLING_BLOCKED, attach only the HTTP status and provider error code; owner may complete Business Information and Payment Methods, then a *new*, specifically authorized probe can be run with a new probe ID.

Hackathon submission deadline: 2026-11-04 21:00 Ecuador.
