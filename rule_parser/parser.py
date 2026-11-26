"""Parse readable Turing Machine rules into a deterministic lookup map.

Grammar::

    current_state, read_symbol -> next_state, write_symbol, direction

A hash starts a comment. Blank lines are ignored. Symbols are one character
long and directions are L (left), R (right), or S (stay).
"""

from __future__ import annotations

from typing import TypeAlias

from .exceptions import (
    DuplicateTransitionError,
    InvalidDirectionError,
    RuleSyntaxError,
)

TransitionValue: TypeAlias = dict[str, str]
TransitionMap: TypeAlias = dict[tuple[str, str], TransitionValue]
_ALLOWED_DIRECTIONS = {"L", "R", "S"}


def _one_character(value: str, field_name: str, line_number: int) -> None:
    if len(value) != 1:
        raise RuleSyntaxError(
            f"{field_name} must be exactly one character; received {value!r}.",
            line_number,
        )


def parse_rules(rule_text: str) -> TransitionMap:
    """Parse rules into a map keyed by ``(current_state, read_symbol)``.

    Args:
        rule_text: Newline-separated transition rules. Lines may contain
            comments beginning with ``#``.

    Returns:
        A dictionary whose values contain ``next_state``, ``write_symbol``,
        and ``direction``. This is the lookup shape specified in the project
        README and can be used directly by the TM execution engine.

    Raises:
        TypeError: If ``rule_text`` is not a string.
        RuleSyntaxError: If a non-comment line has invalid syntax or symbols.
        InvalidDirectionError: If a direction is not L, R, or S.
        DuplicateTransitionError: If a key is defined more than once.
    """
    if not isinstance(rule_text, str):
        raise TypeError("rule_text must be a string")

    transition_map: TransitionMap = {}

    for line_number, original_line in enumerate(rule_text.splitlines(), start=1):
        # Remove comments first, then ignore whitespace-only lines.
        line = original_line.split("#", 1)[0].strip()
        if not line:
            continue

        if line.count("->") != 1:
            raise RuleSyntaxError(
                "Expected exactly one '->' separating the current and next configuration.",
                line_number,
            )

        left_text, right_text = (part.strip() for part in line.split("->", 1))
        left_parts = [part.strip() for part in left_text.split(",")]
        right_parts = [part.strip() for part in right_text.split(",")]

        if len(left_parts) != 2 or len(right_parts) != 3:
            raise RuleSyntaxError(
                "Expected 'current_state, read_symbol -> next_state, write_symbol, direction'.",
                line_number,
            )

        current_state, read_symbol = left_parts
        next_state, write_symbol, direction = right_parts

        if not current_state or not next_state:
            raise RuleSyntaxError("State names must be non-empty.", line_number)
        if any(not value for value in (read_symbol, write_symbol, direction)):
            raise RuleSyntaxError("Read symbol, write symbol, and direction cannot be empty.", line_number)

        _one_character(read_symbol, "Read symbol", line_number)
        _one_character(write_symbol, "Write symbol", line_number)

        if direction not in _ALLOWED_DIRECTIONS:
            raise InvalidDirectionError(
                f"Invalid direction {direction!r}; expected one of L, R, or S.",
                line_number,
            )

        key = (current_state, read_symbol)
        if key in transition_map:
            raise DuplicateTransitionError(
                f"Duplicate transition for state {current_state!r} and symbol {read_symbol!r}.",
                line_number,
            )

        transition_map[key] = {
            "next_state": next_state,
            "write_symbol": write_symbol,
            "direction": direction,
        }

    return transition_map
