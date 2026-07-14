"""
hooks.py — Day 4: Hook system for the agent.
Provides:
  - a hook registry (register_hook / fire) for pre_tool and post_tool events
  - built-in logging hooks that write JSONL to tool_calls.log
  - a @hooked_tool decorator for wrapping individual tool functions
"""

import json
import time
import functools
from datetime import datetime, timezone

LOG_FILE = "tool_calls.log"


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_event(event: dict) -> None:
    """Append one JSON line to the log file."""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")


# ---------------- Hook registry ----------------
_hooks = {
    "pre_tool": [],
    "post_tool": [],
}


def register_hook(event_name: str, fn) -> None:
    """Attach a function to a lifecycle event."""
    if event_name not in _hooks:
        _hooks[event_name] = []
    _hooks[event_name].append(fn)


def fire(event_name: str, **payload) -> None:
    """Run all hooks registered for this event."""
    for fn in _hooks.get(event_name, []):
        try:
            fn(**payload)
        except Exception as e:
            # A broken hook should never crash the agent
            print(f"[hook error] {event_name}/{fn.__name__}: {e}")


# ---------------- Built-in logging hooks ----------------
def log_pre_tool(tool_name, arguments, **_):
    log_event(
        {
            "ts": _timestamp(),
            "event": "pre_tool",
            "tool": tool_name,
            "args": arguments,
        }
    )


def log_post_tool(tool_name, arguments, result, duration_s, error=None, **_):
    log_event(
        {
            "ts": _timestamp(),
            "event": "post_tool",
            "tool": tool_name,
            "args": arguments,
            "duration_s": round(duration_s, 3),
            "ok": error is None,
            "error": error,
            "result_preview": str(result)[:200],
        }
    )


register_hook("pre_tool", log_pre_tool)
register_hook("post_tool", log_post_tool)


# ---------------- Decorator version ----------------
def hooked_tool(fn):
    """Wrap any tool function so pre/post hooks fire around it."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        tool_name = fn.__name__
        arguments = {"args": list(args), "kwargs": kwargs}
        fire("pre_tool", tool_name=tool_name, arguments=arguments)
        start = time.perf_counter()
        result, error = None, None
        try:
            result = fn(*args, **kwargs)
            return result
        except Exception as e:
            error = repr(e)
            raise
        finally:
            fire(
                "post_tool",
                tool_name=tool_name,
                arguments=arguments,
                result=result,
                duration_s=time.perf_counter() - start,
                error=error,
            )

    return wrapper
