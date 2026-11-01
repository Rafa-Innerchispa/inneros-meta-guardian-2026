#!/usr/bin/env python3
"""CLI utility to execute a governed one-shot inference against Meta Muse Spark 1.3."""
from __future__ import annotations

import argparse
import json
import sys
from inneros_meta_guardian.meta_once import MetaOnceOperator


def main() -> None:
    parser = argparse.ArgumentParser(description="Execute a governed one-shot Meta Muse Spark inference")
    parser.add_argument("grant_token", help="Single-use grant token (grant_...)")
    parser.add_argument("incident_json", help="Path to incident JSON or inline JSON string")
    parser.add_argument("--memory-json", default="[]", help="Path to verified memory JSON or inline JSON string")
    args = parser.parse_args()

    # Load incident
    if args.incident_json.startswith("{"):
        incident = json.loads(args.incident_json)
    else:
        with open(args.incident_json, "r", encoding="utf-8") as f:
            incident = json.load(f)

    # Load memory
    if args.memory_json.startswith("["):
        memory = json.loads(args.memory_json)
    else:
        with open(args.memory_json, "r", encoding="utf-8") as f:
            memory = json.load(f)

    operator = MetaOnceOperator()
    try:
        receipt = operator.execute_inference(
            grant_token=args.grant_token,
            incident_telemetry=incident,
            historical_memory=memory,
        )
        print(json.dumps(receipt, indent=2, ensure_ascii=False))
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
