import os
import shutil
import time
import threading
from pathlib import Path
from typing import Optional, Tuple
from pymongo import UpdateOne
from bson import ObjectId

def resolve_gitdir(path: Path) -> Path:
    """Resolve gitdir links in worktrees."""
    if path.is_file() and path.read_text().strip().startswith('gitdir:'):
        return Path(path.read_text().strip()[7:].strip())
    return path

def is_remote_host(host: str) -> bool:
    """Check if host is remote."""
    return host != "localhost" and host != os.getenv("HOSTNAME", "")

def validate_and_recover_task(
    task_id: str,
    claim_host: str,
    current_host: str,
    pid: Optional[int],
    lease_until: float,
    heartbeat: Optional[float],
    revision: int,
    db_collection,
    remote_liveness_verifier=None
) -> bool:
    # 1. Validate host match before PID checks
    if is_remote_host(claim_host) and claim_host != current_host:
        if not remote_liveness_verifier:
            return False
        if not remote_liveness_verifier(claim_host, pid):
            return False
    elif pid is not None:
        try:
            os.kill(pid, 0)
            return False  # Active PID
        except OSError:
            pass  # No process, proceed

    # 2. Resolve linked worktree gitdirs
    worktree_path = Path("/worktrees") / task_id
    git_dir = resolve_gitdir(worktree_path / ".git")
    lock_file = git_dir / "index.lock"

    # 3. Check for active lock
    if lock_file.exists():
        return False

    # 4. Enforce atomic CAS
    result = db_collection.update_one({
        "_id": task_id,
        "revision": revision,
        "status": {"$in": ["awaiting_antigravity_claim", "awaiting_cursor_claim"]}
    }, {
        "$set": {
            "status": "awaiting_claim",
            "lease_until": time.time() + 300,
            "revision": revision + 1
        }
    })

    if result.modified_count != 1:
        return False

    # 5. Skip if active heartbeat or PID
    if heartbeat and time.time() - heartbeat < 180:
        return False
    if pid is not None:
        try:
            os.kill(pid, 0)
            return False
        except OSError:
            pass

    return True

# Example usage
if __name__ == "__main__":
    # Mock DB collection
    class MockCollection:
        def update_one(self, filter, update):
            self.last_filter = filter
            self.last_update = update
            return type('MockResult', (), {'modified_count': 1})()

    db = MockCollection()
    assert validate_and_recover_task(
        "ops_4e977fd8ec43",
        "ralfiia-amd",
        "ralfiia-amd",
        None,
        time.time() - 1000,
        None,
        1,
        db
    )