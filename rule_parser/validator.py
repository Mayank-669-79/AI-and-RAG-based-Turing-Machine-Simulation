"""Validate Turing Machine definitions against the shared project contract."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from .exceptions import MachineValidationError

_REQUIRED_MACHINE_FIELDS = (
    "states", "input_alphabet", "tape_alphabet", "blank_symbol",
    "start_state", "accept_states", "reject_states", "transitions",
)
_ALLOWED_DIRECTIONS = {"L", "R", "S"}


def _string_list(value: Any, field_name: str, *, symbols: bool = False) -> list[str]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise MachineValidationError(f"'{field_name}' must be a list of strings.")
    result = list(value)
    if any(not isinstance(item, str) or not item for item in result):
        raise MachineValidationError(f"Every item in '{field_name}' must be a non-empty string.")
    if len(result) != len(set(result)):
        raise MachineValidationError(f"'{field_name}' must not contain duplicates.")
    if symbols and any(len(item) != 1 for item in result):
        raise MachineValidationError(f"Every symbol in '{field_name}' must be exactly one character.")
    return result


def _normalize_transitions(raw: Any) -> list[dict[str, str]]:
    """Accept the README machine list or the parser's keyed lookup map."""
    normalized: list[dict[str, str]] = []

    if isinstance(raw, Mapping):
        items = []
        for key, value in raw.items():
            if not isinstance(key, tuple) or len(key) != 2:
                raise MachineValidationError(
                    "Transition-map keys must be (current_state, read_symbol) tuples."
                )
            if not isinstance(value, Mapping):
                raise MachineValidationError("Each transition-map value must be a mapping.")
            items.append({
                "current_state": key[0],
                "read_symbol": key[1],
                "next_state": value.get("next_state"),
                "write_symbol": value.get("write_symbol"),
                "direction": value.get("direction"),
            })
    elif isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
        items = list(raw)
    else:
        raise MachineValidationError("'transitions' must be a list or a parsed transition map.")

    seen: set[tuple[str, str]] = set()
    required = ("current_state", "read_symbol", "next_state", "write_symbol", "direction")
    for index, item in enumerate(items):
        if not isinstance(item, Mapping):
            raise MachineValidationError(f"Transition at index {index} must be an object.")
        missing = [field for field in required if field not in item]
        if missing:
            raise MachineValidationError(
                f"Transition at index {index} is missing: {', '.join(missing)}."
            )
        values = {field: item[field] for field in required}
        for field in ("current_state", "next_state"):
            if not isinstance(values[field], str) or not values[field].strip():
                raise MachineValidationError(
                    f"Transition at index {index}: '{field}' must be a non-empty string."
                )
        for field in ("read_symbol", "write_symbol"):
            if not isinstance(values[field], str) or len(values[field]) != 1:
                raise MachineValidationError(
                    f"Transition at index {index}: '{field}' must be exactly one character."
                )
        if not isinstance(values["direction"], str) or values["direction"] not in _ALLOWED_DIRECTIONS:
            raise MachineValidationError(
                f"Transition at index {index}: direction must be L, R, or S."
            )
        key = (values["current_state"], values["read_symbol"])
        if key in seen:
            raise MachineValidationError(
                f"Duplicate transition for state {key[0]!r} and symbol {key[1]!r}."
            )
        seen.add(key)
        normalized.append(values)

    return normalized


def validate_machine(machine: dict) -> dict:
    """Validate a machine and return a normalized, independent copy.

    The function accepts the machine dictionary defined in the root README.
    Its ``transitions`` value may be either the documented list of transition
    objects or the lookup map returned by :func:`parse_rules`.

    The returned machine keeps the documented list representation in
    ``transitions`` and additionally exposes ``transition_map`` for efficient
    deterministic lookup. The original input dictionary is not mutated.

    Raises:
        MachineValidationError: If any required field, state, alphabet, or
            transition violates the project contract.
    """
    if not isinstance(machine, dict):
        raise MachineValidationError("Machine definition must be a dictionary.")

    missing = [field for field in _REQUIRED_MACHINE_FIELDS if field not in machine]
    if missing:
        raise MachineValidationError(
            f"Machine is missing required field(s): {', '.join(missing)}."
        )

    states = _string_list(machine["states"], "states")
    input_alphabet = _string_list(machine["input_alphabet"], "input_alphabet", symbols=True)
    tape_alphabet = _string_list(machine["tape_alphabet"], "tape_alphabet", symbols=True)
    accept_states = _string_list(machine["accept_states"], "accept_states")
    reject_states = _string_list(machine["reject_states"], "reject_states")

    state_set = set(states)
    tape_set = set(tape_alphabet)

    if not isinstance(machine["blank_symbol"], str) or len(machine["blank_symbol"]) != 1:
        raise MachineValidationError("'blank_symbol' must be exactly one character.")
    blank_symbol = machine["blank_symbol"]
    if blank_symbol not in tape_set:
        raise MachineValidationError("Blank symbol must belong to the tape alphabet.")

    if not set(input_alphabet).issubset(tape_set):
        invalid = sorted(set(input_alphabet) - tape_set)
        raise MachineValidationError(
            f"Input alphabet must be a subset of the tape alphabet; invalid symbol(s): {invalid}."
        )

    start_state = machine["start_state"]
    if not isinstance(start_state, str) or start_state not in state_set:
        raise MachineValidationError("Start state must be declared in 'states'.")

    undeclared_accept = sorted(set(accept_states) - state_set)
    if undeclared_accept:
        raise MachineValidationError(f"Accept state(s) not declared: {undeclared_accept}.")
    undeclared_reject = sorted(set(reject_states) - state_set)
    if undeclared_reject:
        raise MachineValidationError(f"Reject state(s) not declared: {undeclared_reject}.")
    overlap = sorted(set(accept_states) & set(reject_states))
    if overlap:
        raise MachineValidationError(
            f"Accept and reject states must not overlap; overlapping state(s): {overlap}."
        )

    transitions = _normalize_transitions(machine["transitions"])
    transition_map: dict[tuple[str, str], dict[str, str]] = {}

    for index, transition in enumerate(transitions):
        current_state = transition["current_state"]
        next_state = transition["next_state"]
        read_symbol = transition["read_symbol"]
        write_symbol = transition["write_symbol"]

        if current_state not in state_set:
            raise MachineValidationError(
                f"Transition at index {index}: current state {current_state!r} is not declared."
            )
        if next_state not in state_set:
            raise MachineValidationError(
                f"Transition at index {index}: next state {next_state!r} is not declared."
            )
        if read_symbol not in tape_set:
            raise MachineValidationError(
                f"Transition at index {index}: read symbol {read_symbol!r} is not in the tape alphabet."
            )
        if write_symbol not in tape_set:
            raise MachineValidationError(
                f"Transition at index {index}: write symbol {write_symbol!r} is not in the tape alphabet."
            )

        transition_map[(current_state, read_symbol)] = {
            "next_state": next_state,
            "write_symbol": write_symbol,
            "direction": transition["direction"],
        }

    validated = deepcopy(machine)
    validated["states"] = states
    validated["input_alphabet"] = input_alphabet
    validated["tape_alphabet"] = tape_alphabet
    validated["accept_states"] = accept_states
    validated["reject_states"] = reject_states
    validated["transitions"] = transitions
    validated["transition_map"] = transition_map
    return validated
