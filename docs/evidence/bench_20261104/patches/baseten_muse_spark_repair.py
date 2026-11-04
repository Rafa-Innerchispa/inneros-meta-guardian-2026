Fixed 5 defects: host-gated PID check, gitdir file resolution, CAS with modified_count, awaiting claim precedence, heartbeat/PID guard.

```python
# ops_interactive_recovery.py
# InnerOS - Interactive Claim Lease Recovery (production-ready)
# Fixes: DEFECT_02, DEFECT_03, DEFECT_04, DEFECT_05
import os
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Callable, Dict, Any

logger = logging.getLogger(__name__)

HEARTBEAT_THRESHOLD_S = 180

# ---------------------------------------------------------------------------
# Liveness helpers - DEFECT_02 + DEFECT_05
# ---------------------------------------------------------------------------

def is_pid_alive_local(pid: int) -> bool:
    """Check local PID liveness via os.kill(pid,0). Returns False on invalid pid."""
    if pid is None:
        return False
    try:
        pid = int(pid)
    except (ValueError, TypeError):
        return False
    if pid <= 0:
        return