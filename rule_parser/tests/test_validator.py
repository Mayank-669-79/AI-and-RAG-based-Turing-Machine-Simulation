from copy import deepcopy

import pytest

from rule_parser import MachineValidationError, parse_rules, validate_machine


@pytest.fixture
def valid_machine():
    return {
        "states": ["q0", "q_accept", "q_reject"],
        "input_alphabet": ["0", "1"],
        "tape_alphabet": ["0", "1", "B"],
        "blank_symbol": "B",
        "start_state": "q0",
        "accept_states": ["q_accept"],
        "reject_states": ["q_reject"],
        "transitions": [
            {
                "current_state": "q0", "read_symbol": "0",
                "next_state": "q0", "write_symbol": "0", "direction": "R",
            },
            {
                "current_state": "q0", "read_symbol": "1",
                "next_state": "q_accept", "write_symbol": "1", "direction": "S",
            },
        ],
    }


def test_valid_machine_returns_copy_and_lookup_map(valid_machine):
    original = deepcopy(valid_machine)
    result = validate_machine(valid_machine)
    assert result is not valid_machine
    assert valid_machine == original
    assert result["transition_map"][("q0", "0")] == {
        "next_state": "q0", "write_symbol": "0", "direction": "R"
    }


def test_parser_lookup_map_can_be_validated(valid_machine):
    valid_machine["transitions"] = parse_rules("q0, 0 -> q0, 0, R")
    result = validate_machine(valid_machine)
    assert result["transitions"][0]["current_state"] == "q0"


def test_missing_required_field_is_rejected(valid_machine):
    del valid_machine["start_state"]
    with pytest.raises(MachineValidationError, match="start_state"):
        validate_machine(valid_machine)


def test_undeclared_start_state_is_rejected(valid_machine):
    valid_machine["start_state"] = "q_missing"
    with pytest.raises(MachineValidationError, match="Start state"):
        validate_machine(valid_machine)


def test_undeclared_accept_state_is_rejected(valid_machine):
    valid_machine["accept_states"] = ["q_missing"]
    with pytest.raises(MachineValidationError, match="not declared"):
        validate_machine(valid_machine)


def test_accept_reject_overlap_is_rejected(valid_machine):
    valid_machine["reject_states"] = ["q_accept"]
    with pytest.raises(MachineValidationError, match="must not overlap"):
        validate_machine(valid_machine)


def test_input_alphabet_must_be_subset_of_tape_alphabet(valid_machine):
    valid_machine["input_alphabet"] = ["0", "1", "x"]
    with pytest.raises(MachineValidationError, match="subset"):
        validate_machine(valid_machine)


def test_blank_symbol_must_be_in_tape_alphabet(valid_machine):
    valid_machine["blank_symbol"] = "_"
    with pytest.raises(MachineValidationError, match="Blank symbol"):
        validate_machine(valid_machine)


def test_undeclared_transition_state_is_rejected(valid_machine):
    valid_machine["transitions"][0]["next_state"] = "q_missing"
    with pytest.raises(MachineValidationError, match="next state"):
        validate_machine(valid_machine)


def test_transition_symbol_must_be_in_tape_alphabet(valid_machine):
    valid_machine["transitions"][0]["read_symbol"] = "x"
    with pytest.raises(MachineValidationError, match="read symbol"):
        validate_machine(valid_machine)


def test_duplicate_transition_key_is_rejected(valid_machine):
    valid_machine["transitions"].append(deepcopy(valid_machine["transitions"][0]))
    with pytest.raises(MachineValidationError, match="Duplicate transition"):
        validate_machine(valid_machine)


def test_invalid_direction_is_rejected(valid_machine):
    valid_machine["transitions"][0]["direction"] = "UP"
    with pytest.raises(MachineValidationError, match="direction"):
        validate_machine(valid_machine)


def test_non_dictionary_machine_is_rejected():
    with pytest.raises(MachineValidationError, match="dictionary"):
        validate_machine([])
