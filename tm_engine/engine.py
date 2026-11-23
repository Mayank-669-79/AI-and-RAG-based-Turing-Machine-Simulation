"""Single-step deterministic Turing Machine execution."""
from __future__ import annotations
from typing import Any, Mapping
from .tape import Tape


def transition_lookup(machine: Mapping[str, Any]) -> dict[tuple[str, str], dict[str, str]]:
    """Normalize either a transition list or parser-style tuple-keyed map."""
    raw = machine.get("transitions", {})
    lookup: dict[tuple[str, str], dict[str, str]] = {}
    if isinstance(raw, Mapping):
        for key, value in raw.items():
            if isinstance(key, tuple) and len(key) == 2:
                state, symbol = key
            elif isinstance(key, str) and "," in key:
                state, symbol = (part.strip() for part in key.split(",", 1))
            else:
                raise ValueError(f"Invalid transition key: {key!r}")
            rule = dict(value)
            lookup[(str(state), str(symbol))] = _normalize_rule(rule)
    elif isinstance(raw, (list, tuple)):
        for rule in raw:
            if not isinstance(rule, Mapping):
                raise ValueError("Each transition must be a mapping")
            state = rule.get("current_state", rule.get("state"))
            symbol = rule.get("read_symbol", rule.get("read"))
            if state is None or symbol is None:
                raise ValueError("Transition requires current_state and read_symbol")
            key = (str(state), str(symbol))
            if key in lookup:
                raise ValueError(f"Duplicate transition for {key!r}")
            lookup[key] = _normalize_rule(rule)
    else:
        raise ValueError("machine.transitions must be a list or mapping")
    return lookup


def _normalize_rule(rule: Mapping[str, Any]) -> dict[str, str]:
    next_state = rule.get("next_state")
    write_symbol = rule.get("write_symbol", rule.get("write"))
    direction = rule.get("direction", rule.get("move"))
    if next_state is None or write_symbol is None or direction is None:
        raise ValueError("Transition requires next_state, write_symbol, and direction")
    direction = str(direction).upper()
    if direction not in {"L", "R", "S"}:
        raise ValueError(f"Invalid transition direction: {direction!r}")
    return {"next_state": str(next_state), "write_symbol": str(write_symbol), "direction": direction}


def execute_step(machine: Mapping[str, Any], state: str, tape: Tape,
                 transitions: dict[tuple[str, str], dict[str, str]] | None = None
                 ) -> dict[str, Any]:
    """Execute one transition, returning pre-transition read and new config.

    Raises ``KeyError`` if no transition is defined for this configuration.
    """
    transitions = transitions if transitions is not None else transition_lookup(machine)
    read_symbol = tape.read()
    rule = transitions.get((state, read_symbol))
    if rule is None:
        raise KeyError((state, read_symbol))
    write_symbol = rule["write_symbol"]
    direction = rule["direction"]
    tape.write(write_symbol)
    tape.move(direction)
    return {
        "state": rule["next_state"], "read": read_symbol,
        "write": write_symbol, "move": direction,
        "head_position": tape.head_position, "tape": tape.snapshot(),
    }
