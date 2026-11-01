#!/usr/bin/env python3
"""CLI utility for operator to issue a single-use grant bound to a snapshot digest."""
from __future__ import annotations

import argparse
import json
import sys
from inneros_meta_guardian.meta_once import GRANT_STORE


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a single-use Meta Muse Spark inference grant")
    parser.add_argument("snapshot_digest", help="64-character SHA-256 digest of the incident snapshot")
    parser.add_argument("--ttl", type=int, default=300, help="Grant TTL in seconds (default 300)")
    parser.add_argument("--max-tokens", type=int, default=400, help="Max tokens allowed (default 400)")
    parser.add_argument("--model", default="muse-spark-1.3", help="Target Meta model")
    args = parser.parse_args()

    try:
        grant = GRANT_STORE.create_grant(
            snapshot_digest=args.snapshot_digest,
            ttl_seconds=args.ttl,
            max_tokens=args.max_tokens,
            model=args.model,
        )
        print(json.dumps(grant, indent=2))
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
