"""Trace records for deterministic Turing Machine execution."""
from __future__ import annotations
from typing import Any


def make_trace_record(*, step: int, state: str, head: int, read: str,
                      write: str | None, move: str | None,
                      tape: list[str]) -> dict[str, Any]:
    """Build a stable public trace record; tape is copied to prevent mutation."""
    return {
        "step": step,
        "state": state,
        "head": head,
        "read": read,
        "write": write,
        "move": move,
        "tape": tape.copy(),
    }
