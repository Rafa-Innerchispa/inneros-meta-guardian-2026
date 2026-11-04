"""Recovery for orphaned manual / interactive IDE ops tasks."""

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

ORPHAN_STATUSES = ("accepted", "in_progress", "running", "claimed")
DEFAULT_HEARTBEAT_MAX_AGE_SECONDS = 180


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def requires_manual_interactive_lane(task: dict[str, Any]) -> bool:
    if task.get("do_not_auto_dispatch") is True:
        return True
    lane = str(task.get("execution_lane") or "").strip().lower()
    if lane in MANUAL_INTERACTIVE_LANES or lane.endswith("_interactive"):
        return True
    binding = ((task.get("evidence") or {}).get("execution_binding") or {})
    if binding.get("interactive_execution") is True:
        return True
    return False


def _usable_worktree(task: dict[str, Any]) -> bool:
    wt = task.get("worktree") or task.get("local_worktree")
    if not wt:
        return False
    try:
        return Path(str(wt)).is_dir()
    except OSError:
        return False


def _is_worktree_git_locked(wt_path: Path) -> bool:
    """Resolve .git directory or linked worktree .git pointer file and detect active index.lock."""
    try:
        if (wt_path / "index.lock").exists():
            return True
        dot_git = wt_path / ".git"
        if dot_git.is_dir():
            return (dot_git / "index.lock").exists()
        if dot_git.is_file():
            content = dot_git.read_text(encoding="utf-8", errors="replace")
            for raw_line in content.splitlines():
                line = raw_line.strip()
                if line.lower().startswith("gitdir:"):
                    raw_gitdir = line.split(":", 1)[1].strip()
                    if not raw_gitdir:
                        continue
                    gitdir_path = Path(raw_gitdir)
                    if not gitdir_path.is_absolute():
                        gitdir_path = (wt_path / gitdir_path).resolve()
                    if (gitdir_path / "index.lock").exists():
                        return True
    except OSError:
        return True
    return False


def _has_recent_heartbeat(task: dict[str, Any], *, max_age_seconds: int = DEFAULT_HEARTBEAT_MAX_AGE_SECONDS) -> bool:
    hb_raw = task.get("heartbeat_at") or task.get("last_heartbeat_at") or task.get("worker_heartbeat_at")
    hb_dt = _parse_ts(str(hb_raw or ""))
    if hb_dt is None:
        return False
    now = datetime.now(timezone.utc)
    age = (now - hb_dt).total_seconds()
    return age < max_age_seconds


def _is_local_pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True
    except (ProcessLookupError, OSError):
        return False


def _check_safety_preconditions(
    task: dict[str, Any],
    *,
    remote_liveness_verifier: Callable[[str, int | None], bool] | None = None,
    heartbeat_max_age_seconds: int = DEFAULT_HEARTBEAT_MAX_AGE_SECONDS,
) -> tuple[bool, str]:
    """Return (can_recover, skip_reason). Guaranteed zero database mutations."""
    if _has_recent_heartbeat(task, max_age_seconds=heartbeat_max_age_seconds):
        return False, "recent_heartbeat"

    wt = task.get("worktree") or task.get("local_worktree")
    if wt:
        try:
            wt_path = Path(str(wt))
            if wt_path.exists() and _is_worktree_git_locked(wt_path):
                return False, "worktree_git_locked"
        except OSError:
            return False, "worktree_git_locked"

    claim_host = str(task.get("claim_host") or task.get("headless_execution_host") or "").strip()
    raw_pid = task.get("headless_execution_pid") or task.get("worker_pid") or task.get("pid")
    pid: int | None = None
    if raw_pid is not None and str(raw_pid).strip() != "":
        try:
            pid = int(raw_pid)
        except (TypeError, ValueError):
            pid = None

    local_host = socket.gethostname().strip()
    is_remote_host = bool(
        claim_host
        and claim_host.lower() not in {local_host.lower(), "localhost", "127.0.0.1"}
    )

    if is_remote_host:
        if remote_liveness_verifier is None:
            return False, f"remote_host_unverified:{claim_host}"
        try:
            remote_alive = remote_liveness_verifier(claim_host, pid)
        except Exception:
            return False, f"remote_host_unverified:{claim_host}"
        if remote_alive is not False:
            return False, f"remote_host_active:{claim_host}"
    else:
        if pid is not None and pid > 0 and _is_local_pid_alive(pid):
            return False, f"active_local_pid:{pid}"

    return True, "ok"


def has_active_valid_claim(task: dict[str, Any], *, grace_seconds: int = 30) -> bool:
    token = (task.get("claim_token") or "").strip()
    if not token:
        return False
    lease = _parse_ts(str(task.get("lease_until") or ""))
    if lease is None:
        return True
    now = datetime.now(timezone.utc)
    if lease > now:
        return True
    return (now - lease).total_seconds() <= grace_seconds


def external_repair_may_auto_claim(task: dict[str, Any]) -> tuple[bool, str]:
    if task.get("do_not_auto_dispatch") is True:
        return False, "do_not_auto_dispatch"
    if requires_manual_interactive_lane(task):
        return False, "manual_interactive_lane"
    return True, "ok"


def recover_orphan_interactive_ops_tasks(
    limit: int = 20,
    *,
    remote_liveness_verifier: Callable[[str, int | None], bool] | None = None,
    heartbeat_max_age_seconds: int = DEFAULT_HEARTBEAT_MAX_AGE_SECONDS,
) -> dict[str, Any]:
    db = mongo_store.get_db()
    filt = {
        "status": {"$in": list(ORPHAN_STATUSES)},
    }
    rows = list(
        db[OPS_TASKS_COL]
        .find(filt, {"_id": 0})
        .sort("updated_at", 1)
        .limit(max(5, min(limit * 4, 80)))
    )
    recovered: list[dict[str, Any]] = []
    skipped_active: list[dict[str, Any]] = []
    cas_conflicts: list[dict[str, Any]] = []

    for task in rows:
        if len(recovered) >= limit:
            break
        if not requires_manual_interactive_lane(task):
            continue
        if has_active_valid_claim(task):
            continue

        tid = str(task.get("task_id") or "")
        if not tid:
            continue

        # CRITICAL INVARIANT: Verify all safety preconditions BEFORE any database write
        can_recover, skip_reason = _check_safety_preconditions(
            task,
            remote_liveness_verifier=remote_liveness_verifier,
            heartbeat_max_age_seconds=heartbeat_max_age_seconds,
        )
        if not can_recover:
            skipped_active.append({"task_id": tid, "reason": skip_reason})
            continue

        target = awaiting_claim_status_for_task(task)
        now = _now()

        cas_filter: dict[str, Any] = {
            "task_id": tid,
            "status": task.get("status", "claimed"),
            "claim_token": task.get("claim_token"),
            "lease_until": task.get("lease_until"),
        }
        if "revision" in task and task.get("revision") is not None:
            cas_filter["revision"] = task["revision"]

        res = db[OPS_TASKS_COL].update_one(
            cas_filter,
            {
                "$set": {
                    "status": target,
                    "updated_at": now,
                    "claim_error": "orphan_interactive_recovered",
                    "orphan_recovery_at": now,
                },
                "$unset": {
                    "claim_token": "",
                    "claimed_at": "",
                    "lease_until": "",
                    "claimed_by": "",
                    "claim_host": "",
                    "headless_execution_started_at": "",
                    "headless_execution_pid": "",
                    "headless_execution_host": "",
                },
                "$inc": {"revision": 1},
            },
        )
        if getattr(res, "modified_count", 0) == 1:
            recovered.append({"task_id": tid, "status": target})
        else:
            cas_conflicts.append({"task_id": tid, "reason": "cas_conflict"})

    return {
        "ok": True,
        "recovered": recovered,
        "skipped_active": skipped_active,
        "cas_conflicts": cas_conflicts,
        "scanned": len(rows),
    }
