import functools
import time
from typing import Any

audit_log: list[dict[str, Any]] = []


def audited(fn):
    """Logs every call: tool name, args, duration, and a result preview.
    Required on every tool — see CLAUDE.md conventions."""

    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await fn(*args, **kwargs)
        audit_log.append(
            {
                "tool": fn.__name__,
                "args": kwargs,
                "duration_ms": round((time.time() - start) * 1000, 1),
                "result_preview": str(result)[:200],
            }
        )
        return result

    return wrapper
