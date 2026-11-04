"""Qwen3-Coder-30B Corrected Drop-in Repair (Assisted v2).

Fixes the critical safety flaw identified in qwen_local_repair.py where
database mutation occurred prior to checking worker heartbeat.
Conforms strictly to inneros_core_runtime.ops_interactive_recovery.
"""
from __future__ import annotations

import os
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from inneros_core_runtime.coordination_live import OPS_TASKS_COL
from inneros_core_runtime.ops_awaiting_claim import awaiting_claim_status_for_task
from raphiia_openai import mongo_store

MANUAL_INTERACTIVE_LANES = frozenset(
    {
        "local_manual_antigravity",
        "manual_interactive",
        "antigravity_interactive",
        "cursor_interactive",
        "codex_interactive",
        "gemini_interactive",
    }
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _local_host_aliases() -> set[str]:
    local_names = {"localhost", "127.0.0.1", "::1"}
    try:
        local_names.add(socket.gethostname().strip().lower())
    except Exception:
        pass
    env_host = os.getenv("HOSTNAME", "").strip().lower()
    if env_host:
        local_names.add(env_host)
    return local_names


def _resolve_git_lock_paths(worktree_path: Path) -> list[Path]:
    git_ref = worktree_path / ".git"
    candidates: list[Path] = []
    if git_ref.is_dir():
        candidates.append(git_ref / "index.lock")
    elif git_ref.is_file():
        try:
            content = git_ref.read_text(encoding="utf-8").strip()
            if content.startswith("gitdir:"):
                raw_target = content[len("gitdir:"):].strip()
                target_path = Path(raw_target)
                if not target_path.is_absolute():
                    target_path = (worktree_path / target_path).resolve()
                candidates.append(target_path / "index.lock")
        except OSError:
            pass
    return candidates


def is_worker_active(task: dict[str, Any], *, remote_liveness_verifier: Callable[[str, int | None], bool] | None = None) -> tuple[bool, str]:
    # 1. Heartbeat check (fresh < 180s) -> active
    hb = _parse_ts(task.get("heartbeat_at"))
    if hb:
        delta = (datetime.now(timezone.utc) - hb).total_seconds()
        if delta < 180:
            return True, f"recent_heartbeat:{int(delta)}s"

    # 2. Cross-host check -> fail closed if on remote host
    task_host = str(task.get("claim_host") or task.get("headless_execution_host") or "").strip().lower()
    if task_host and task_host not in _local_host_aliases():
        if not task.get("remote_worker_verified_absent"):
            if remote_liveness_verifier is None or remote_liveness_verifier(task_host, task.get("headless_execution_pid")) is not False:
                return True, f"remote_host_unverified:{task_host}"

    # 3. Local OS PID check
    pid = task.get("headless_execution_pid")
    if pid:
        try:
            pid_int = int(pid)
            os.kill(pid_int, 0)
            return True, f"process_alive:{pid_int}"
        except OSError:
            pass

    # 4. Worktree git lock check
    wt = task.get("worktree")
    if wt:
        wt_path = Path(str(wt))
        for lock in _resolve_git_lock_paths(wt_path):
            if lock.exists():
                return True, f"git_lock_present:{lock}"

    return False, "inactive"


def recover_orphan_interactive_ops_tasks(
    limit: int = 10,
    *,
    remote_liveness_verifier: Callable[[str, int | None], bool] | None = None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    db = mongo_store.get_db()
    col = db[OPS_TASKS_COL]

    query = {
        "status": "claimed",
        "$or": [
            {"execution_lane": {"$in": list(MANUAL_INTERACTIVE_LANES)}},
            {"do_not_auto_dispatch": True},
        ],
    }

    candidates = list(col.find(query).sort("claimed_at", 1).limit(limit * 2))
    recovered: list[dict[str, Any]] = []

    for task in candidates:
        if len(recovered) >= limit:
            break

        lease_ts = _parse_ts(task.get("lease_until"))
        if not lease_ts or lease_ts > now:
            continue  # lease not expired

        # CRITICAL SAFETY PRE-CONDITION: Verify worker inactive BEFORE any DB mutation
        active, reason = is_worker_active(task, remote_liveness_verifier=remote_liveness_verifier)
        if active:
            continue

        target_status = awaiting_claim_status_for_task(task)
        filter_doc: dict[str, Any] = {
            "task_id": task["task_id"],
            "status": "claimed",
            "claim_token": task.get("claim_token"),
            "lease_until": task.get("lease_until"),
        }
        if "revision" in task:
            filter_doc["revision"] = task["revision"]

        update_doc: dict[str, Any] = {
            "$set": {
                "status": target_status,
                "updated_at": _now(),
            },
            "$unset": {
                "claim_token": "",
                "lease_until": "",
                "claimed_at": "",
            },
        }
        if "revision" in task:
            update_doc["$inc"] = {"revision": 1}

        res = col.update_one(filter_doc, update_doc)
        if res.modified_count == 1:
            recovered.append({
                "task_id": task["task_id"],
                "status": target_status,
                "recovered_at": _now(),
            })

    return {"ok": True, "recovered": recovered, "limit": limit}

