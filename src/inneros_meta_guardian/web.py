"""Stdlib HTTP app for InnerOS Autonomous Infrastructure Guardian.
Provides REST API and web console for live judge demonstration.
Supports HTTP Basic Auth / query token for Judge Access.
"""
from __future__ import annotations

import base64
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .baseten_adapter import BasetenAdapter
from .diagnostic_orchestrator import ORCHESTRATOR, OrchestratorError
from .engine import Guardian, LifecycleError
from .fireworks_adapter import FireworksAdapter
from .integrations import VoiceOpsRecordedReceipt
from .meta_once import GRANT_STORE, GrantError
from .meta_registry import MetaProviderRegistry
from .modal_sandbox_adapter import ModalSandboxAdapter
from .provider_finance import ProviderFinanceManager
from .repair_evaluator import RepairEvaluator
from .sam_inspector import SAMInspector
from .selfheal_lab import SelfHealingLab, LabError, case_evidence

STATIC = Path(__file__).parent / "static"


class Handler(BaseHTTPRequestHandler):
    guardian: Guardian
    selfheal_lab = SelfHealingLab()  # process-local, isolated demo only
    orchestrator = ORCHESTRATOR
    finance_manager = ProviderFinanceManager()
    server_version = "InnerOSMetaGuardian/1.3"

    def _write(self, status: int, content: bytes, mime: str = "application/json; charset=utf-8", extra_headers: list[tuple[str, str]] | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
        )
        if extra_headers:
            for k, v in extra_headers:
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(content)

    def _json(self, status: int, obj: dict) -> None:
        self._write(status, json.dumps(obj, ensure_ascii=False).encode())

    def _body(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise LifecycleError("Invalid Content-Length") from None
        if length <= 0 or length > 32768:
            raise LifecycleError("Request body required; maximum 32 KiB")
        try:
            val = json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            raise LifecycleError("Invalid JSON body") from None
        if not isinstance(val, dict):
            raise LifecycleError("JSON object required")
        return val

    def _check_auth(self) -> bool:
        """Enforces judge authentication when GUARDIAN_REQUIRE_AUTH=true."""
        auth_required = os.getenv("GUARDIAN_REQUIRE_AUTH", "false").lower() in ("true", "1", "yes")
        if not auth_required or os.getenv("GUARDIAN_NO_AUTH", "false").lower() in ("true", "1", "yes"):
            return True

        path = urlsplit(self.path).path
        query = parse_qs(urlsplit(self.path).query)

        # Health endpoint remains public for Cloudflare monitoring and uptime checks
        if path == "/api/health":
            return True

        # Check token in query string: ?auth=MetaGuardian2026! or ?auth=meta2026
        token_param = query.get("auth", [""])[0] or query.get("token", [""])[0]
        if token_param in ("MetaGuardian2026!", "meta2026", "inneros2026"):
            return True

        # Check Cookie: inneros_auth=MetaGuardian2026
        cookies = self.headers.get("Cookie", "")
        if "inneros_auth=MetaGuardian2026" in cookies or "inneros_auth=meta2026" in cookies:
            return True

        # Check HTTP Basic Auth header: Authorization: Basic <base64>
        auth_hdr = self.headers.get("Authorization", "")
        if auth_hdr.startswith("Basic "):
            try:
                decoded = base64.b64decode(auth_hdr[6:].strip()).decode("utf-8")
                user, _, password = decoded.partition(":")
                valid_pass = os.getenv("GUARDIAN_JUDGE_PASS", "MetaGuardian2026!")
                allowed_users = ("judge", "inneros", "admin", "rafael")
                if user in allowed_users and password == valid_pass:
                    return True
            except Exception:
                pass

        # Send HTTP 401 Challenge with Realm
        msg = (
            b"<!doctype html><html><body style='background:#080d17;color:#edf4ff;font-family:sans-serif;padding:40px;'>"
            b"<h2>InnerOS Autonomous Infrastructure Guardian</h2>"
            b"<p>Judge and Operator Authentication Required.</p>"
            b"<p>Username: <code>judge</code> (or <code>inneros</code>)<br>Password: <code>MetaGuardian2026!</code></p>"
            b"<p><a href='/self-heal?auth=MetaGuardian2026!' style='color:#6ccbf6;'>Or click here to enter with 1-click token</a></p>"
            b"</body></html>"
        )
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="InnerOS Autonomous Infrastructure Guardian (Judge Access)"')
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(msg)))
        self.end_headers()
        self.wfile.write(msg)
        return False

    def do_HEAD(self):  # noqa: N802
        if not self._check_auth():
            return
        self.do_GET()

    def do_GET(self):  # noqa: N802
        if not self._check_auth():
            return

        path = urlsplit(self.path).path
        query = parse_qs(urlsplit(self.path).query)
        cookie_header = None
        if query.get("auth", [""])[0] in ("MetaGuardian2026!", "meta2026"):
            cookie_header = [("Set-Cookie", "inneros_auth=MetaGuardian2026; Path=/; SameSite=Lax")]

        if path in ("/", "/index.html"):
            self._static("index.html", "text/html; charset=utf-8", cookie_header)
        elif path == "/app.js":
            self._static("app.js", "application/javascript; charset=utf-8")
        elif path == "/styles.css":
            self._static("styles.css", "text/css; charset=utf-8")
        elif path in ("/self-heal", "/self-heal.html"):
            self._static("self-heal.html", "text/html; charset=utf-8", cookie_header)
        elif path == "/self-heal.js":
            self._static("self-heal.js", "application/javascript; charset=utf-8")
        elif path == "/self-heal.css":
            self._static("self-heal.css", "text/css; charset=utf-8")
        elif path == "/api/selfheal/case":
            self._json(200, case_evidence())
        elif path == "/api/meta/ecosystem":
            self._json(200, RepairEvaluator.get_ecosystem_inventory())
        elif path == "/api/meta/providers":
            self._json(200, MetaProviderRegistry.list_providers())
        elif path == "/api/meta/benchmark":
            self._json(200, RepairEvaluator.get_benchmark_comparison())
        elif path == "/api/meta/finance":
            self._json(200, self.finance_manager.generate_financial_matrix())
        elif path == "/api/meta/dossier":
            self._json(200, RepairEvaluator.get_unified_dossier())
        elif path == "/api/orchestrator/snapshot":
            self._json(200, self.orchestrator.get_global_snapshot())
        elif path.startswith("/api/orchestrator/sessions/") and len(path.strip("/").split("/")) == 4:
            sid = path.strip("/").split("/")[3]
            try:
                self._json(200, self.orchestrator.get_session(sid))
            except OrchestratorError as exc:
                self._json(404, {"error": str(exc)})
        elif path.startswith("/api/selfheal/labs/") and path.endswith("/evidence"):
            parts = path.strip("/").split("/")
            if len(parts) != 5:
                self._json(404, {"error": "Not found"})
            else:
                try:
                    self._json(200, self.selfheal_lab.evidence(parts[3]))
                except LabError as exc:
                    self._json(404, {"error": str(exc)})
        elif path == "/api/health":
            public_mode = os.getenv("GUARDIAN_PUBLIC_MODE", "false").lower() in ("true", "1", "yes")
            self._json(
                200,
                {
                    "ok": True,
                    "version": "1.3.0",
                    "project": "InnerOS Autonomous Infrastructure Guardian",
                    "hackathon": "Meta Global AI Developer Hackathon 2026",
                    "track": "Startup Track (Push the Frontier)",
                    "mode": "PUBLIC_JUDGE_DEMO" if public_mode else "PRIVATE_OPERATOR_LAB",
                    "public_mode": public_mode,
                    "auth_enabled": os.getenv("GUARDIAN_REQUIRE_AUTH", "false").lower() in ("true", "1", "yes"),
                    "physical_actions_live": False,
                    "meta_supported": True,
                    "meta_status": "HISTORICAL_EVIDENCE_AND_CLI_INSTALLED",
                    "meta_live_api_active": False,
                    "financial_matrix_available": True,
                    "unified_dossier_available": True,
                    "provider_finance": {
                        "fireworks_status": "TESTED_LIVE",
                        "fireworks_receipt": "docs/evidence/fireworks_live_receipt_20261104.json",
                        "baseten_status": "TESTED_LIVE",
                        "baseten_receipt": "docs/evidence/baseten_live_receipt_20261104.json",
                        "modal_status": "TESTED_LIVE",
                        "modal_receipt": "docs/evidence/modal_live_receipt_20261104.json",
                        "unapproved_cloud_spend_usd": 0.0,
                    },
                    "meta_evidence": {
                        "wonder_investigation": "VERIFIED_2_TURN_TOOL_RECEIPT",
                        "wonder_session_resp": "resp_6aea97477ecbaecc16a14e99 -> resp_6aea97f2ad831065ca8b4bc8",
                        "cli_version": "1.4.14-R7309.1",
                        "cli_status": "INSTALLED_LOCAL_CLI",
                        "auth_status": "BLOCKED_AWAITING_OWNER_AUTH",
                        "unapproved_cloud_spend_usd": 0.0,
                    },
                    "comparative_benchmark": {
                        "argon_repair": "VERIFIED_PASS_10_OF_10_GREEN",
                        "argon_commit": "94d90d34",
                        "qwen_local_rocm": "ONLINE_SOVEREIGN_AWQ",
                        "gpt6_astra": "BLOCKED_API_ACCESS",
                    },
                    "public_url": "https://guardian.pcdoctor.ai/self-heal",
                },
            )
        elif path == "/api/state":
            self._json(
                200,
                {
                    "scenarios": self.guardian.scenarios,
                    "incidents": self.guardian.store.list_incidents(),
                    "audit_integrity": self.guardian.store.verify(),
                    "mode": "GOVERNED_INFRASTRUCTURE_DEMO",
                    "project": "InnerOS Autonomous Infrastructure Guardian",
                },
            )
        elif path == "/api/audit/verify":
            self._json(200, self.guardian.store.verify())
        elif path == "/api/voiceops/receipt":
            self._json(200, VoiceOpsRecordedReceipt.get_verified_call_receipt())
        elif path == "/api/sam/inspect":
            qs = parse_qs(urlsplit(self.path).query)
            asset = qs.get("asset", ["lab_rack_switch_led"])[0]
            self._json(200, self.guardian.sam_inspector.inspect_lab_asset(asset))
        elif path.startswith("/api/incidents/") and path.endswith("/evidence"):
            id_val = path.split("/")[3]
            try:
                self._json(200, self.guardian.evidence(id_val))
            except LifecycleError as exc:
                self._json(404, {"error": str(exc)})
        elif path.startswith("/api/incidents/") and len(path.split("/")) == 4:
            id_val = path.split("/")[3]
            try:
                self._json(200, self.guardian.get(id_val))
            except LifecycleError as exc:
                self._json(404, {"error": str(exc)})
        else:
            self._json(404, {"error": "Not found"})

    def _static(self, filename: str, mime: str, extra_headers: list[tuple[str, str]] | None = None) -> None:
        file_path = STATIC / filename
        if not file_path.is_file():
            self._json(404, {"error": "File not found"})
            return
        self._write(200, file_path.read_bytes(), mime, extra_headers=extra_headers)

    def do_POST(self):  # noqa: N802
        if not self._check_auth():
            return

        path = urlsplit(self.path).path
        try:
            body = self._body() if self.headers.get("Content-Length") else {}

            public_mode = os.getenv("GUARDIAN_PUBLIC_MODE", "false").lower() in ("true", "1", "yes")
            if public_mode:
                if path in (
                    "/api/orchestrator/investigate",
                    "/api/incidents",
                    "/api/incidents/live",
                    "/api/grants",
                ) or path.startswith("/api/incidents/"):
                    self._json(403, {
                        "error": "PUBLIC_READ_ONLY_MODE: Privileged mutation and live investigation endpoints are disabled in public judge demo. Please inspect the recorded forensic evidence and benchmarks.",
                        "mode": "PUBLIC_JUDGE_DEMO",
                        "public_mode": True,
                    })
                    return

            # Offline Dry-Run Contract Verification (allowed in public mode since it spends $0.00)
            if path == "/api/meta/finance/dryrun":
                provider = str(body.get("provider") or "fireworks_ai")
                if provider == "fireworks_ai":
                    adapter = FireworksAdapter(finance_manager=self.finance_manager)
                    res = adapter.complete(
                        messages=[{"role": "user", "content": "Dry-run sanitized coordination evaluation"}],
                        dry_run=True,
                    )
                elif provider == "baseten":
                    adapter = BasetenAdapter(finance_manager=self.finance_manager)
                    res = adapter.complete(
                        messages=[{"role": "user", "content": "Dry-run sanitized coordination evaluation"}],
                        dry_run=True,
                    )
                elif provider == "modal":
                    adapter = ModalSandboxAdapter(finance_manager=self.finance_manager)
                    res = adapter.run_isolated_test(
                        test_script_content="pytest tests/test_ops_expired_claim_lease_recovery.py",
                        files_manifest={"test_ops.py": "pass"},
                        dry_run=True,
                    )
                else:
                    self._json(400, {"error": f"Unknown provider for dry run: {provider}"})
                    return
                self._json(200, res)
                return

            # Autonomous tool-calling diagnostic orchestrator (read-only + simulation tools, zero paid calls)
            if path == "/api/orchestrator/investigate":
                session = self.orchestrator.start_investigation(
                    prompt=str(body.get("prompt") or ""),
                    engine_mode=str(body.get("engine_mode") or "hybrid_comparison"),
                    max_tool_calls=int(body.get("max_tool_calls", 6)),
                    max_tokens=int(body.get("max_tokens", 4096)),
                    max_cost_usd=float(body.get("max_cost_usd", 0.50)),
                )
                self._json(201, session)
                return

            if path.startswith("/api/orchestrator/sessions/") and path.endswith("/cancel"):
                parts = path.strip("/").split("/")
                if len(parts) != 5:
                    self._json(404, {"error": "Not found"})
                    return
                self._json(200, self.orchestrator.cancel_session(
                    parts[3], reason=str(body.get("reason") or "operator_cancelled")
                ))
                return

            # Separate demo-only self-healing replay. No real agents or model calls.
            if path == "/api/selfheal/labs":
                self._json(201, self.selfheal_lab.start(
                    scenario=str(body.get("scenario") or "stale_agent_claim"),
                ))
                return
            if path.startswith("/api/selfheal/labs/") and path.endswith("/transition"):
                parts = path.strip("/").split("/")
                if len(parts) != 5:
                    self._json(404, {"error": "Not found"})
                    return
                self._json(200, self.selfheal_lab.transition(
                    parts[3], action=str(body.get("action") or ""),
                    actor=str(body.get("actor") or ""),
                ))
                return

            # 1. Ingest simulated scenario
            if path == "/api/incidents":
                scenario = body.get("scenario", "door_propped")
                self._json(201, self.guardian.ingest(scenario))
                return

            # 2. Ingest LIVE infrastructure reading
            if path == "/api/incidents/live":
                site = body.get("site", "casa")
                category = body.get("category", "network")
                incident = self.guardian.ingest_live(site=site, category=category)
                self._json(201, incident)
                return

            # 3. Create single-use Meta grant
            if path == "/api/grants":
                self._json(403, {"error": "META_OPERATOR_ONLY: no grant creation from unauthenticated web UI."})
                return

            # 4. Incident lifecycle actions: /api/incidents/{id}/{action}
            parts = path.strip("/").split("/")
            if len(parts) == 4 and parts[:2] == ["api", "incidents"]:
                _, _, incident_id, action = parts
                if action == "remember":
                    query = body.get("query", "")
                    result = self.guardian.remember(incident_id, query=query)
                elif action == "analyze":
                    mode = body.get("mode", "deterministic")
                    if mode == "meta":
                        self._json(403, {"error": "META_OPERATOR_ONLY: paid inference disabled over web HTTP API."})
                        return
                    grant_token = body.get("grant_token")
                    result = self.guardian.analyze(incident_id, mode=mode, grant_token=grant_token)
                elif action == "approve":
                    operator = body.get("operator", "")
                    action_name = body.get("action", "")
                    result = self.guardian.approve(incident_id, operator, action_name)
                elif action == "execute":
                    result = self.guardian.execute(incident_id)
                elif action == "verify":
                    result = self.guardian.verify(incident_id)
                else:
                    self._json(404, {"error": f"Unknown action '{action}'"})
                    return
                self._json(200, result)
                return

            self._json(404, {"error": "Unknown route"})
        except (LifecycleError, GrantError, LabError, OrchestratorError, ValueError) as exc:
            self._json(409, {"error": str(exc)})
        except Exception as exc:
            self._json(500, {"error": f"Internal application error: {type(exc).__name__}"})

    def log_message(self, format: str, *args) -> None:
        if os.getenv("GUARDIAN_ACCESS_LOG", "false").lower() == "true":
            super().log_message(format, *args)


def serve(host: str | None = None, port: int | None = None, db: str | None = None) -> None:
    host = host or os.getenv("HOST", "127.0.0.1")
    port = int(port or os.getenv("PORT", "8787"))
    if host not in ("127.0.0.1", "localhost", "::1") and os.getenv("GUARDIAN_UNSAFE_BIND") != "true":
        raise SystemExit("Refusing public bind without GUARDIAN_UNSAFE_BIND=true.")
    database = db or os.getenv("GUARDIAN_DB", "runtime/guardian.db")
    guardian = Guardian(database)

    class ServerHandler(Handler):
        pass

    ServerHandler.guardian = guardian
    server = ThreadingHTTPServer((host, port), ServerHandler)
    print(f"InnerOS Meta Guardian demo running at http://{host}:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    serve()
