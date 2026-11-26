"""Deterministic Turing Machine construction for supported language conditions."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any, Literal, TypedDict


START_STATE = "q0"
ACCEPT_STATE = "q_accept"
REJECT_STATE = "q_reject"
BLANK_SYMBOL = "B"

Direction = Literal["L", "R", "S"]


class MachineBuildError(ValueError):
    """Raised when a valid machine cannot be constructed."""


class Transition(TypedDict):
    """Transition rule for a deterministic Turing Machine."""

    current_state: str
    read_symbol: str
    next_state: str
    write_symbol: str
    direction: Direction


class MachineDefinition(TypedDict):
    """Machine definition shared with the parser and execution engine."""

    states: list[str]
    input_alphabet: list[str]
    tape_alphabet: list[str]
    blank_symbol: str
    start_state: str
    accept_states: list[str]
    reject_states: list[str]
    transitions: list[Transition]


class MachineBuilder:
    """Construct a deterministic machine using reusable transition utilities."""

    def __init__(self, alphabet: Sequence[str]) -> None:
        self.alphabet = list(alphabet)
        self.states = [START_STATE, ACCEPT_STATE, REJECT_STATE]
        self.transitions: list[Transition] = []
        self._transition_keys: set[tuple[str, str]] = set()

    def add_state(self, state: str) -> None:
        """Register a state if it does not already exist."""

        if state not in self.states:
            self.states.append(state)

    def add_transition(
        self,
        current_state: str,
        read_symbol: str,
        next_state: str,
        direction: Direction = "R",
    ) -> None:
        """Register a deterministic transition without modifying tape content."""

        key = (current_state, read_symbol)

        if key in self._transition_keys:
            raise MachineBuildError(
                f"Duplicate transition for state '{current_state}' "
                f"and symbol '{read_symbol}'."
            )

        self.add_state(current_state)
        self.add_state(next_state)

        self.transitions.append(
            {
                "current_state": current_state,
                "read_symbol": read_symbol,
                "next_state": next_state,
                "write_symbol": read_symbol,
                "direction": direction,
            }
        )

        self._transition_keys.add(key)

    def add_halt_transition(
        self,
        state: str,
        accepted: bool,
    ) -> None:
        """Define the halting transition when the input ends."""

        target = ACCEPT_STATE if accepted else REJECT_STATE

        self.add_transition(
            current_state=state,
            read_symbol=BLANK_SYMBOL,
            next_state=target,
            direction="S",
        )

    def build(self) -> MachineDefinition:
        """Return the machine using the project's shared definition schema."""

        return {
            "states": self.states.copy(),
            "input_alphabet": self.alphabet.copy(),
            "tape_alphabet": [*self.alphabet, BLANK_SYMBOL],
            "blank_symbol": BLANK_SYMBOL,
            "start_state": START_STATE,
            "accept_states": [ACCEPT_STATE],
            "reject_states": [REJECT_STATE],
            "transitions": [
                transition.copy()
                for transition in self.transitions
            ],
        }


def _validate_alphabet(value: Any) -> list[str]:
    """Validate the input alphabet and reserve the blank symbol."""

    if not isinstance(value, (list, tuple)) or not value:
        raise MachineBuildError(
            "The input alphabet must be a non-empty sequence."
        )

    if any(
        not isinstance(symbol, str) or len(symbol) != 1
        for symbol in value
    ):
        raise MachineBuildError(
            "Alphabet symbols must be single-character strings."
        )

    if len(set(value)) != len(value):
        raise MachineBuildError(
            "The input alphabet contains duplicate symbols."
        )

    if BLANK_SYMBOL in value:
        raise MachineBuildError(
            f"'{BLANK_SYMBOL}' is reserved as the blank symbol."
        )

    return list(value)


def _get_string_parameter(
    parameters: Mapping[str, Any],
    name: str,
) -> str:
    """Retrieve and validate a required string parameter."""

    value = parameters.get(name)

    if not isinstance(value, str):
        raise MachineBuildError(
            f"Parameter '{name}' must be a string."
        )

    return value


def _get_symbol(
    parameters: Mapping[str, Any],
    name: str,
    alphabet: Sequence[str],
) -> str:
    """Retrieve a symbol belonging to the input alphabet."""

    symbol = _get_string_parameter(parameters, name)

    if symbol not in alphabet:
        raise MachineBuildError(
            f"Parameter '{name}' contains an invalid symbol: '{symbol}'."
        )

    return symbol


def _get_pattern(
    parameters: Mapping[str, Any],
    name: str,
    alphabet: Sequence[str],
) -> str:
    """Retrieve a string containing only valid alphabet symbols."""

    pattern = _get_string_parameter(parameters, name)

    if any(symbol not in alphabet for symbol in pattern):
        raise MachineBuildError(
            f"Parameter '{name}' contains symbols outside the alphabet."
        )

    return pattern


def _get_parity(parameters: Mapping[str, Any]) -> str:
    """Validate the requested parity."""

    parity = _get_string_parameter(parameters, "parity")

    if parity not in {"even", "odd"}:
        raise MachineBuildError(
            "Parity must be either 'even' or 'odd'."
        )

    return parity


def _build_starts_with(
    builder: MachineBuilder,
    parameters: Mapping[str, Any],
) -> None:
    """Construct a machine that accepts strings starting with a symbol."""

    symbol = _get_symbol(parameters, "symbol", builder.alphabet)

    for character in builder.alphabet:
        target = "q1" if character == symbol else REJECT_STATE

        builder.add_transition(START_STATE, character, target)
        builder.add_transition("q1", character, "q1")

    builder.add_halt_transition(START_STATE, accepted=False)
    builder.add_halt_transition("q1", accepted=True)


def _build_ends_with(
    builder: MachineBuilder,
    parameters: Mapping[str, Any],
) -> None:
    """Construct a machine that tracks the most recently read symbol."""

    symbol = _get_symbol(parameters, "symbol", builder.alphabet)

    for state in (START_STATE, "q1"):
        for character in builder.alphabet:
            target = "q1" if character == symbol else START_STATE

            builder.add_transition(state, character, target)

        builder.add_halt_transition(
            state,
            accepted=(state == "q1"),
        )


def _build_substring_machine(
    builder: MachineBuilder,
    parameters: Mapping[str, Any],
    *,
    accept_when_found: bool,
) -> None:
    """Construct a substring machine supporting overlapping matches."""

    pattern = _get_pattern(
        parameters,
        "substring",
        builder.alphabet,
    )

    pattern_length = len(pattern)

    for matched_length in range(pattern_length + 1):
        state = f"q{matched_length}"

        for character in builder.alphabet:
            if matched_length == pattern_length:
                next_length = pattern_length
            else:
                candidate = pattern[:matched_length] + character
                next_length = min(pattern_length, len(candidate))

                # Retain the longest suffix matching a pattern prefix.
                while next_length > 0:
                    if candidate.endswith(pattern[:next_length]):
                        break

                    next_length -= 1

            builder.add_transition(
                state,
                character,
                f"q{next_length}",
            )

        pattern_found = matched_length == pattern_length

        builder.add_halt_transition(
            state,
            accepted=(pattern_found == accept_when_found),
        )


def _build_contains(
    builder: MachineBuilder,
    parameters: Mapping[str, Any],
) -> None:
    """Accept strings containing the requested substring."""

    _build_substring_machine(
        builder,
        parameters,
        accept_when_found=True,
    )


def _build_does_not_contain(
    builder: MachineBuilder,
    parameters: Mapping[str, Any],
) -> None:
    """Accept strings that do not contain the requested substring."""

    _build_substring_machine(
        builder,
        parameters,
        accept_when_found=False,
    )


def _build_parity_machine(
    builder: MachineBuilder,
    parity: str,
    symbol: str | None = None,
) -> None:
    """Track even and odd counts using two alternating states."""

    accepting_state = START_STATE if parity == "even" else "q1"

    for state, alternate_state in (
        (START_STATE, "q1"),
        ("q1", START_STATE),
    ):
        for character in builder.alphabet:
            should_toggle = symbol is None or character == symbol

            target = alternate_state if should_toggle else state

            builder.add_transition(state, character, target)

        builder.add_halt_transition(
            state,
            accepted=(state == accepting_state),
        )


def _build_length_parity(
    builder: MachineBuilder,
    parameters: Mapping[str, Any],
) -> None:
    """Accept strings having the requested length parity."""

    _build_parity_machine(
        builder,
        parity=_get_parity(parameters),
    )


def _build_count_parity(
    builder: MachineBuilder,
    parameters: Mapping[str, Any],
) -> None:
    """Accept strings having the requested symbol-count parity."""

    symbol = _get_symbol(parameters, "symbol", builder.alphabet)

    _build_parity_machine(
        builder,
        parity=_get_parity(parameters),
        symbol=symbol,
    )


def _build_starts_and_ends(
    builder: MachineBuilder,
    parameters: Mapping[str, Any],
) -> None:
    """Accept strings satisfying both boundary conditions."""

    start_symbol = _get_symbol(
        parameters,
        "start_symbol",
        builder.alphabet,
    )

    end_symbol = _get_symbol(
        parameters,
        "end_symbol",
        builder.alphabet,
    )

    for character in builder.alphabet:
        if character != start_symbol:
            target = REJECT_STATE
        elif character == end_symbol:
            target = "q2"
        else:
            target = "q1"

        builder.add_transition(START_STATE, character, target)

    for state in ("q1", "q2"):
        for character in builder.alphabet:
            target = "q2" if character == end_symbol else "q1"

            builder.add_transition(state, character, target)

    builder.add_halt_transition(START_STATE, accepted=False)
    builder.add_halt_transition("q1", accepted=False)
    builder.add_halt_transition("q2", accepted=True)


def _build_exact_string(
    builder: MachineBuilder,
    parameters: Mapping[str, Any],
) -> None:
    """Accept only the specified string."""

    expected = _get_pattern(
        parameters,
        "value",
        builder.alphabet,
    )

    for position in range(len(expected) + 1):
        state = f"q{position}"

        for character in builder.alphabet:
            if position < len(expected) and character == expected[position]:
                target = f"q{position + 1}"
            else:
                target = REJECT_STATE

            builder.add_transition(state, character, target)

        builder.add_halt_transition(
            state,
            accepted=(position == len(expected)),
        )


def _build_empty_or_nonempty(
    builder: MachineBuilder,
    parameters: Mapping[str, Any],
) -> None:
    """Accept empty or non-empty strings according to the requested mode."""

    mode = _get_string_parameter(parameters, "mode")

    if mode not in {"empty", "nonempty"}:
        raise MachineBuildError(
            "Mode must be either 'empty' or 'nonempty'."
        )

    for character in builder.alphabet:
        builder.add_transition(START_STATE, character, "q1")
        builder.add_transition("q1", character, "q1")

    builder.add_halt_transition(
        START_STATE,
        accepted=(mode == "empty"),
    )

    builder.add_halt_transition(
        "q1",
        accepted=(mode == "nonempty"),
    )


TemplateHandler = Callable[
    [MachineBuilder, Mapping[str, Any]],
    None,
]


_TEMPLATE_REGISTRY: dict[str, TemplateHandler] = {
    "starts_with": _build_starts_with,
    "ends_with": _build_ends_with,
    "contains": _build_contains,
    "does_not_contain": _build_does_not_contain,
    "length_parity": _build_length_parity,
    "count_parity": _build_count_parity,
    "starts_and_ends": _build_starts_and_ends,
    "exact_string": _build_exact_string,
    "empty_or_nonempty": _build_empty_or_nonempty,
}


def build_machine(
    normalized_condition: Mapping[str, Any],
    retrieved_context: Sequence[Mapping[str, Any]] | None = None,
) -> MachineDefinition:
    """Construct a deterministic machine from a normalized condition.

    Args:
        normalized_condition: Structured condition produced by the
            NLP interpreter.
        retrieved_context: Optional RAG construction knowledge.
            Reserved for integration with the retrieval pipeline.

    Returns:
        A machine definition compatible with the rule validator
        and Turing Machine execution engine.

    Raises:
        MachineBuildError: If the condition is unsupported, ambiguous,
            or contains invalid parameters.

    Notes:
        Retrieved content does not directly modify transition rules.
        Machine construction uses deterministic templates only.
    """

    if not isinstance(normalized_condition, Mapping):
        raise MachineBuildError(
            "The normalized condition must be a mapping."
        )

    if normalized_condition.get("needs_clarification"):
        raise MachineBuildError(
            "The condition requires clarification before construction."
        )

    family = normalized_condition.get("family")

    if not isinstance(family, str) or family not in _TEMPLATE_REGISTRY:
        raise MachineBuildError(
            f"Unsupported condition family: {family!r}."
        )

    parameters = normalized_condition.get("parameters")

    if not isinstance(parameters, Mapping):
        raise MachineBuildError(
            "Condition parameters must be a mapping."
        )

    alphabet = _validate_alphabet(
        normalized_condition.get("alphabet", ["0", "1"])
    )

    builder = MachineBuilder(alphabet)

    template_handler = _TEMPLATE_REGISTRY[family]
    template_handler(builder, parameters)

    return builder.build()