import urllib.request
import json
import time
import hashlib
from datetime import datetime, timezone

PROMPT = """You are an expert distributed systems and Python engineer analyzing InnerOS agent coordination failures.
Fictional lab scenario only: no customer credentials, private IPs, or production secrets.

INCIDENT REPORT:
1. Coordination Defect:
A task is trapped in status 'claimed' with an expired lease (lease_until < now).
In 'ops_interactive_recovery.py', the existing recovery logic releases the task by clearing claim_token and claimed_by without verifying if the worker process is actually dead.
When a worker is still alive (e.g. executing a long test suite), clearing its claim causes concurrent execution by another agent and duplicate task runs.
Furthermore, concurrent lease renewals or competing recovery processes cause race conditions when CAS updates only check the claim token without verifying revision, status, lease, and modified_count == 1.

2. Trust Boundary Gate Defect:
In 'test_provider_execution_trust_boundary.py', execution_resource_guard lifecycle admission rejects the task with 'resource_task_not_executable' before reaching the 'owner_budget_grant_required' barrier because the test fixture omitted 'status: claimed'.

REQUIRED ANALYSIS:
Please provide:
1. ROOT CAUSE ANALYSIS: Explain why expired lease != dead worker, and why CAS updates must be atomic and multi-field.
2. REMEDIATION PLAN: Outline the minimal, surgical safeguards in Python (checking worker PID via os.kill, heartbeats, git index locks, and multi-field CAS with modified_count == 1).
3. SAFETY INVARIANT: Explain why zero writes on active workers prevents cascade failures.
"""

prompt_sha256 = hashlib.sha256(PROMPT.encode("utf-8")).hexdigest()
url = "http://127.0.0.1:8000/v1/chat/completions"
model_name = "QuantTrio/Qwen3-Coder-30B-A3B-Instruct-AWQ"

payload = {
    "model": model_name,
    "messages": [
        {"role": "system", "content": "You are InnerOS Local Diagnostic Engine powered by Qwen3-Coder-30B."},
        {"role": "user", "content": PROMPT}
    ],
    "max_tokens": 1024,
    "temperature": 0.2
}

print(f"Sending prompt (SHA-256: {prompt_sha256}) to local Qwen at {url}...")
start_time = time.time()
req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

with urllib.request.urlopen(req, timeout=120) as resp:
    raw_data = resp.read()

latency_ms = int((time.time() - start_time) * 1000)
data = json.loads(raw_data.decode("utf-8"))

usage = data.get("usage", {})
content = data["choices"][0]["message"]["content"]

result = {
    "status": "REAL_SUCCESS",
    "provider": "vllm-rocm-local",
    "model": model_name,
    "hardware": "AMD Radeon AI PRO R9700 (ROCm 10.1)",
    "prompt_sha256": prompt_sha256,
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "latency_ms": latency_ms,
    "usage": {
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens")
    },
    "cost_usd": 0.0,
    "diagnostic_response": content
}

print(f"SUCCESS in {latency_ms} ms! Tokens used: {usage.get('total_tokens')}")
print("\n--- DIAGNOSTIC PREVIEW ---")
print(content[:500] + "...")

output_path = "/tmp/qwen_local_diagnostic_20261103.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
print(f"\nSaved genuine diagnostic to {output_path}")
