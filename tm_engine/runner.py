"""Full deterministic TM execution with halting and step-limit handling."""
from __future__ import annotations
from collections.abc import Mapping
from typing import Any
from .engine import execute_step, transition_lookup
from .tape import Tape
from .trace import make_trace_record


def run_machine(machine: dict[str, Any], input_string: str, max_steps: int = 1000) -> dict[str, Any]:
    """Run a deterministic TM and return status, final configuration, and trace.

    Missing transitions follow this project's convention and reject with reason
    ``missing_transition``. A running machine reaching ``max_steps`` reports
    ``STEP_LIMIT`` and is never mislabeled ACCEPT or REJECT.
    """
    if not isinstance(machine, Mapping):
        raise TypeError("machine must be a mapping")
    if not isinstance(input_string, str):
        raise TypeError("input_string must be a string")
    if isinstance(max_steps, bool) or not isinstance(max_steps, int) or max_steps < 1:
        raise ValueError("max_steps must be a positive integer")
    start_state = machine.get("start_state")
    if not isinstance(start_state, str) or not start_state:
        raise ValueError("machine.start_state must be a non-empty string")
    blank = machine.get("blank_symbol", "B")
    if not isinstance(blank, str) or not blank:
        raise ValueError("machine.blank_symbol must be a non-empty string")
    accept_states = set(machine.get("accept_states", []))
    reject_states = set(machine.get("reject_states", []))
    if accept_states & reject_states:
        raise ValueError("accept_states and reject_states must not overlap")
    tape = Tape(input_string, blank)
    state = start_state
    transitions = transition_lookup(machine)
    trace = [make_trace_record(step=0, state=state, head=tape.head_position,
                               read=tape.read(), write=None, move=None, tape=tape.snapshot())]
    steps = 0
    status, reason = "", ""
    while True:
        if state in accept_states:
            status, reason = "ACCEPT", "accept_state"
            break
        if state in reject_states:
            status, reason = "REJECT", "reject_state"
            break
        if steps >= max_steps:
            status, reason = "STEP_LIMIT", "max_steps"
            break
        try:
            result = execute_step(machine, state, tape, transitions)
        except KeyError:
            status, reason = "REJECT", "missing_transition"
            break
        state = result["state"]
        steps += 1
        trace.append(make_trace_record(step=steps, state=state,
                       head=tape.head_position, read=tape.read(),
                       write=result["write"], move=result["move"], tape=tape.snapshot()))

    return {
        "status": status,
        "reason": reason,
        "steps": steps,
        "final_state": state,
        "final_tape": tape.snapshot(),
        "head_position": tape.head_position,
        "trace": trace,
    }
