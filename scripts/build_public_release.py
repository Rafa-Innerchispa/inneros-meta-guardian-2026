#!/usr/bin/env python3
"""Export a CLEAN, SANITIZED source ZIP without git history.

This does not publish, create repositories or modify their visibility.
Only explicitly vetted source/demo files are copied. No private docs,
messages, receipts, billing, raw telemetry, customer logs or .git metadata.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "inneros_meta_guardian"
TESTS = (
    "tests/test_guardian.py",
    "tests/test_end_to_end_governance.py",
    "tests/test_meta_once.py",
    "tests/test_meta_probe.py",
    "tests/test_sam_visual.py",
    "tests/test_selfheal_lab.py",
    "tests/test_selfheal_web_routes.py",
)
EXTRA = ("Dockerfile", "compose.yaml", "pyproject.toml",
         ".github/workflows/tests.yml", "scripts/run_demo.sh")
REPLACE = (
    ("guardian.creatorcore.ai", "demo-guardian.example.invalid"),
    ("inneros-5-lan", "demo-control-plane.invalid"),
    ("Bellini", "Facility B"),
    ("BELLINI", "FACILITY_B"),
    ("bellini", "facility_b"),
    ("CASA PRIMARY", "DEMO LAB A"),
    ("Casa Primary", "Demo Lab A"),
    ("Casa Network", "Demo Lab Network"),
    ("Casa Servers", "Demo Lab Servers"),
    ("Casa", "Demo Lab"),
    ("rlopez@innerchispa.us", "maintainer@example.invalid"),
)
DENIED = {
    "private IP": re.compile(r"\b(?:192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"),
    "credential-like token": re.compile(r"\b(?:sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})\b"),
    "private hostname": re.compile(r"inneros-5-lan|guardian\.creatorcore\.ai|(?i:bellini)"),
    "personal user path": re.compile(r"/home/rlopez|C:\\Users\\Rafael", re.I),
}
README = """# InnerOS Autonomous Infrastructure Guardian — Meta 2026

Open-source technical demonstration for Meta Global AI Developer Hackathon.

Two experiences: Physical Guardian at / and Self-Healing Mission Control
at /self-heal. No production code changes or paid inference occur in
the web demo. The sanitized physical adapter uses an example.invalid
placeholder; simulated physical incidents still work offline.

The self-healing lab replays an operator-reported Muse Wonder result
and demonstrates a strictly in-memory lifecycle with a lab-only acknowledgement,
virtual patch, independent invariant readback and SHA-256 evidence chain.
The previous Meta provider receipt has not been reconciled with independent
billing or signed owner permission. Real AMD/Qwen comparison for this
exact case is NOT MEASURED. It is not production self-repair.

Run: PYTHONPATH=src python -m inneros_meta_guardian.web
Open: http://127.0.0.1:8787/self-heal
Test: PYTHONPATH=src python -m unittest discover -s tests -v

This clean export excludes proprietary incident reports, private customer
information, secrets, network topology, all unapproved artifacts, and history.
Internal CI references in the demo may not be publicly accessible; no
third-party claims are cryptographically certified by the public ZIP.

Copyright (c) 2026 InnerChispa LLC. Export licensed under MIT; publication
of this source requires the owner's separate approval.
"""
LICENSE = """MIT License

Copyright (c) 2026 InnerChispa LLC

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


def candidates() -> list[Path]:
    base = [p for p in SOURCE.rglob("*") if p.is_file() and p.suffix in (".py", ".js", ".css", ".html")]
    base.extend(ROOT / path for path in TESTS + EXTRA)
    for p in base:
        if not p.is_file():
            raise FileNotFoundError("Missing release input: " + str(p.relative_to(ROOT)))
    return sorted(set(base))


def scrub(text: str) -> str:
    for original, safe in REPLACE:
        text = text.replace(original, safe)
    return text


def verify_public_text(name: str, text: str) -> None:
    if name.startswith(("docs/", "runtime/", ".git/")):
        raise ValueError("Forbidden export path: " + name)
    if "-----BEGIN PRIVATE KEY-----" in text:
        raise ValueError("Private key detected in: " + name)
    for category, pattern in DENIED.items():
        if pattern.search(text):
            raise ValueError("Release guard stopped " + category + " in: " + name)


def create_bundle(path: Path) -> dict:
    content: dict[str, bytes] = {}
    for source in candidates():
        name = source.relative_to(ROOT).as_posix()
        cleaned = scrub(source.read_text(encoding="utf-8"))
        verify_public_text(name, cleaned)
        content[name] = cleaned.encode("utf-8")
    for name, data in (("README.md", README), ("LICENSE", LICENSE)):
        verify_public_text(name, data)
        content[name] = data.encode()
    hashes = {n: hashlib.sha256(data).hexdigest() for n, data in sorted(content.items())}
    manifest = {
        "schema": "inneros.meta.open_source_candidate.v1",
        "source_history_included": False, "production_secrets_included": False,
        "paid_model_calls_enabled": False, "license": "MIT",
        "publication_requires_owner_approval": True, "files": hashes,
    }
    content["PUBLIC_RELEASE_MANIFEST.json"] = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for name, data in sorted(content.items()):
            bundle.writestr(name, data)
    with zipfile.ZipFile(path) as bundle:
        if set(bundle.namelist()) != set(content) or bundle.testzip() is not None:
            raise RuntimeError("Public ZIP archive verification failed")
    return {
        "ok": True, "path": str(path), "files": len(content),
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "license": "MIT; source ZIP is not itself published",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="dist/inneros-meta-open-source-candidate.zip")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        with tempfile.TemporaryDirectory() as tmp:
            result = create_bundle(Path(tmp) / "checked.zip")
    else:
        result = create_bundle(Path(args.output))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
