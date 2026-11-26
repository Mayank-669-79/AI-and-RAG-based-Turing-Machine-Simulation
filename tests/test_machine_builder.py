"""Tests for deterministic machine construction and engine compatibility."""

from itertools import product

import pytest

from api_integration import MachineBuildError, build_machine
from tm_engine import run_machine


@pytest.mark.parametrize(
    "family, parameters, input_string, expected_status",
    [
        # Starts with
        ("starts_with", {"symbol": "1"}, "101", "ACCEPT"),
        ("starts_with", {"symbol": "1"}, "011", "REJECT"),
        ("starts_with", {"symbol": "1"}, "", "REJECT"),

        # Ends with
        ("ends_with", {"symbol": "1"}, "101", "ACCEPT"),
        ("ends_with", {"symbol": "1"}, "110", "REJECT"),
        ("ends_with", {"symbol": "1"}, "", "REJECT"),

        # Contains
        ("contains", {"substring": "101"}, "11010", "ACCEPT"),
        ("contains", {"substring": "101"}, "11100", "REJECT"),
        ("contains", {"substring": "101"}, "", "REJECT"),
        ("contains", {"substring": "101"}, "10101", "ACCEPT"),

        # Does not contain
        ("does_not_contain", {"substring": "11"}, "1010", "ACCEPT"),
        ("does_not_contain", {"substring": "11"}, "1101", "REJECT"),
        ("does_not_contain", {"substring": "11"}, "", "ACCEPT"),

        # Length parity
        ("length_parity", {"parity": "even"}, "1010", "ACCEPT"),
        ("length_parity", {"parity": "even"}, "101", "REJECT"),
        ("length_parity", {"parity": "even"}, "", "ACCEPT"),
        ("length_parity", {"parity": "odd"}, "101", "ACCEPT"),
        ("length_parity", {"parity": "odd"}, "", "REJECT"),

        # Symbol-count parity
        (
            "count_parity",
            {"symbol": "0", "parity": "even"},
            "1001",
            "ACCEPT",
        ),
        (
            "count_parity",
            {"symbol": "0", "parity": "even"},
            "101",
            "REJECT",
        ),
        (
            "count_parity",
            {"symbol": "1", "parity": "odd"},
            "1011",
            "ACCEPT",
        ),
        (
            "count_parity",
            {"symbol": "0", "parity": "even"},
            "",
            "ACCEPT",
        ),

        # Starts and ends
        (
            "starts_and_ends",
            {"start_symbol": "1", "end_symbol": "0"},
            "1010",
            "ACCEPT",
        ),
        (
            "starts_and_ends",
            {"start_symbol": "1", "end_symbol": "0"},
            "0010",
            "REJECT",
        ),
        (
            "starts_and_ends",
            {"start_symbol": "1", "end_symbol": "0"},
            "1011",
            "REJECT",
        ),
        (
            "starts_and_ends",
            {"start_symbol": "1", "end_symbol": "1"},
            "1",
            "ACCEPT",
        ),

        # Exact string
        ("exact_string", {"value": "101"}, "101", "ACCEPT"),
        ("exact_string", {"value": "101"}, "1011", "REJECT"),
        ("exact_string", {"value": "101"}, "10", "REJECT"),
        ("exact_string", {"value": ""}, "", "ACCEPT"),

        # Empty and non-empty
        ("empty_or_nonempty", {"mode": "empty"}, "", "ACCEPT"),
        ("empty_or_nonempty", {"mode": "empty"}, "1", "REJECT"),
        ("empty_or_nonempty", {"mode": "nonempty"}, "0", "ACCEPT"),
        ("empty_or_nonempty", {"mode": "nonempty"}, "", "REJECT"),
    ],
)
def test_machine_execution(
    family: str,
    parameters: dict[str, str],
    input_string: str,
    expected_status: str,
) -> None:
    """Verify generated machines against the actual execution engine."""

    condition = {
        "family": family,
        "parameters": parameters,
        "alphabet": ["0", "1"],
    }

    machine = build_machine(condition)
    result = run_machine(machine, input_string)

    assert result["status"] == expected_status

    expected_reason = (
        "accept_state"
        if expected_status == "ACCEPT"
        else "reject_state"
    )

    assert result["reason"] == expected_reason


@pytest.mark.parametrize(
    "condition",
    [
        {
            "family": "unsupported",
            "parameters": {},
        },
        {
            "family": "starts_with",
            "parameters": {},
        },
        {
            "family": "starts_with",
            "parameters": {"symbol": "2"},
        },
        {
            "family": "length_parity",
            "parameters": {"parity": "invalid"},
        },
        {
            "family": "contains",
            "parameters": {"substring": "102"},
        },
        {
            "family": "ends_with",
            "parameters": {"symbol": "1"},
            "alphabet": [],
        },
        {
            "family": "ends_with",
            "parameters": {"symbol": "1"},
            "alphabet": ["0", "1", "1"],
        },
        {
            "family": "ends_with",
            "parameters": {"symbol": "1"},
            "alphabet": ["0", "1", "B"],
        },
        {
            "family": "ends_with",
            "parameters": {"symbol": "1"},
            "needs_clarification": True,
        },
        {
            "family": "empty_or_nonempty",
            "parameters": {"mode": "invalid"},
        },
        {
            "family": "ends_with",
            "parameters": None,
        },
    ],
)
def test_invalid_conditions(condition: dict) -> None:
    """Ensure invalid conditions fail with a controlled exception."""

    with pytest.raises(MachineBuildError):
        build_machine(condition)


def test_machine_structure() -> None:
    """Verify that the generated machine satisfies structural invariants."""

    machine = build_machine(
        {
            "family": "contains",
            "parameters": {"substring": "101"},
            "alphabet": ["0", "1"],
        }
    )

    states = set(machine["states"])
    tape_alphabet = set(machine["tape_alphabet"])
    accept_states = set(machine["accept_states"])
    reject_states = set(machine["reject_states"])

    assert machine["start_state"] in states
    assert machine["blank_symbol"] in tape_alphabet
    assert machine["blank_symbol"] not in machine["input_alphabet"]

    assert accept_states <= states
    assert reject_states <= states
    assert accept_states.isdisjoint(reject_states)

    transition_keys = set()

    for transition in machine["transitions"]:
        key = (
            transition["current_state"],
            transition["read_symbol"],
        )

        assert key not in transition_keys
        assert transition["current_state"] in states
        assert transition["next_state"] in states
        assert transition["read_symbol"] in tape_alphabet
        assert transition["write_symbol"] in tape_alphabet
        assert transition["direction"] in {"L", "R", "S"}

        assert transition["current_state"] not in accept_states
        assert transition["current_state"] not in reject_states

        transition_keys.add(key)


def test_custom_alphabet() -> None:
    """Verify construction with a non-binary input alphabet."""

    machine = build_machine(
        {
            "family": "ends_with",
            "parameters": {"symbol": "a"},
            "alphabet": ["a", "b"],
        }
    )

    assert run_machine(machine, "bba")["status"] == "ACCEPT"
    assert run_machine(machine, "aab")["status"] == "REJECT"


def test_deterministic_construction() -> None:
    """Identical conditions must produce identical machine definitions."""

    condition = {
        "family": "contains",
        "parameters": {"substring": "101"},
        "alphabet": ["0", "1"],
    }

    assert build_machine(condition) == build_machine(condition)


@pytest.mark.parametrize("pattern", ["", "0", "11", "101", "0101"])
def test_substring_exhaustively(pattern: str) -> None:
    """Compare substring machines against a reference predicate."""

    contains_machine = build_machine(
        {
            "family": "contains",
            "parameters": {"substring": pattern},
        }
    )

    excludes_machine = build_machine(
        {
            "family": "does_not_contain",
            "parameters": {"substring": pattern},
        }
    )

    for length in range(7):
        for symbols in product("01", repeat=length):
            input_string = "".join(symbols)
            contains_pattern = pattern in input_string

            expected_contains = (
                "ACCEPT" if contains_pattern else "REJECT"
            )

            expected_excludes = (
                "REJECT" if contains_pattern else "ACCEPT"
            )

            assert (
                run_machine(contains_machine, input_string)["status"]
                == expected_contains
            )

            assert (
                run_machine(excludes_machine, input_string)["status"]
                == expected_excludes
            )


def test_step_limit_handling() -> None:
    """Ensure incomplete execution is not reported as acceptance."""

    machine = build_machine(
        {
            "family": "length_parity",
            "parameters": {"parity": "even"},
        }
    )

    result = run_machine(machine, "101010", max_steps=2)

    assert result["status"] == "STEP_LIMIT"
    assert result["reason"] == "max_steps"
    assert result["steps"] == 2
