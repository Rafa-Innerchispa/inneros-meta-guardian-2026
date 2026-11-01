# InnerOS Autonomous Infrastructure Guardian | Meta Global AI Developer Hackathon 2026

**From AI that answers to evidence-backed, human-governed infrastructure intelligence.**

![Build status](https://img.shields.io/badge/runtime-Python%203.10%2B-blue) ![Operational truth](https://img.shields.io/badge/demo-synthetic%20only-yellow) ![External spend](https://img.shields.io/badge/Meta%20API-opt--in-green)

> **Hackathon entry, Oct 26 – Nov 4, 2026.** Independent local-first demo for the Meta Global AI Developer Hackathon, built by InnerChispa. This is a new hackathon-specific composition, **not** a claim that InnerOS's earlier work was created during this event. See [PROVENANCE](docs/PROVENANCE.md).

The system turns synthetic observations from cameras, access controls and networks into a governed operational flow:

`OBSERVE → REASON → APPROVE → ACT → VERIFY → PROVE`

The same policy gate is used regardless of which inference provider generates the explanation. The demo **never** operates a real door, camera or building network.

## Live demo locally (zero dependencies)

```bash
cd inneros-meta-guardian-2026
PYTHONPATH=src python -m inneros_meta_guardian.web
```

Open **http://127.0.0.1:8787**. Select a scenario, create an incident, analyze using the deterministic local engine, approve the safe recommended action, execute the virtual actuator, independently verify it, and export a JSON evidence bundle.

Supported scenarios:

1. Pedestrian door propped open, with camera zone occupancy.
2. PoE camera offline, but uplink healthy.
3. Unverified visitor badge event (explicitly **does not open gate**).

## Test without paid APIs

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
# In another terminal after starting the server:
PYTHONPATH=src python scripts/e2e_smoke.py
```

## Optional local Ollama inference

```bash
# Use any locally downloaded Ollama model, e.g. qwen2.5:7b.
export OLLAMA_MODEL=qwen2.5:7b
PYTHONPATH=src python -m inneros_meta_guardian.web
```

Select **Ollama local** in the web UI. Unavailable models fail over to deterministic reasoning with an explicit fallback label. This does not authorize additional operations.

## Meta Model API: currently NOT_RUN

The previous Meta demo option is intentionally disabled in the synthetic web simulator. A source-bound Muse Spark / SAM 3.1 operator adapter must be developed and independently tested before any live paid calls. This recovered baseline has **no verified Meta receipt**, no live Guardian source connection, and no verified Personal Brain memory integration in this app. Do not claim these features in a judge submission until proven.

- https://dev.meta.ai/docs
- https://cerebralvalley.ai/e/meta-ai-developer-hackathon

## Container demo (local loopback only)

```bash
docker compose up --build
```

WebUI is bound to `127.0.0.1:8787` on the host. **Never publish the demo directly to the public Internet**: it intentionally has no login, only synthetic input and in-process virtual actuators. Add authentication and rate limiting before any public judge link. Never enable `GUARDIAN_UNSAFE_BIND` outside an isolated demonstration container or secure reverse proxy.

## Architecture

```
Synthetic incident fixture / future scoped MCP reader
      │
      ▼
Stateful Guardian lifecycle engine ────────→ SQLite incident state
      │                                            │
      ▼                                            ▼
Local deterministic reasoning                SHA-256 audit chain
  ├── optional Ollama local model                  │
  └── external Meta disabled in sandbox                 └── JSON evidence bundle
      │
      ▼
Fixed allowlist + human approval
      │
      ▼
Virtual actuator (NO real I/O)
      │
      ▼
Independent virtual-state readback
```

### What is proven today vs. not yet built

| Capability | Status | Truth label |
|---|---|---|
| Full six-stage demo | Implemented and locally testable | `SIMULATED_FIXTURE` |
| Persistent SQLite incident/audit log | Implemented | `DEMO_HASH_CHAIN_NOT_PRODUCTION_ATTESTATION` |
| Approval/forbidden action policy | Implemented | `DETERMINISTIC_RULE` |
| Virtual actuator and independent in-process readback | Implemented | `SIMULATED_REFERENCE_IO` |
| Ollama local reasoning | Adapter implemented; endpoint not exercised on physical AMD host yet | `LOCAL_MODEL_FROM_SIMULATED_SIGNALS` only when real call succeeds |
| Meta Model API reasoning | NOT_RUN; browser API route disabled until owner-granted operator-only adapter is verified | `NOT_RUN` |
| SAM 3.1 camera segmentation | **Planned, not integrated** | Not claimed |
| Live MCP device read and real hardware readback | **Planned, not integrated** | Not claimed |
| Published external judge URL | **Not deployed** | Not claimed |

## Security and scope

* Fail closed: no gate opening, door unlocking, firewall changes, reboots or shell commands.
* A model's text can never bypass deterministic policy or human approval.
* All incidents are clearly labeled synthetic. Meta and Ollama providers have distinguishable truth labels; fallback is explicitly recorded.
* No biometrics, customer images, credentials or internal network topology in the repository.
* Tests and API use need no external spend by default.

See [architecture](docs/ARCHITECTURE.md), [provenance](docs/PROVENANCE.md), and [submission checklist](docs/SUBMISSION.md).
