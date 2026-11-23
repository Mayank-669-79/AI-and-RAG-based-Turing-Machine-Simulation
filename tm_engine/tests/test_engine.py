import json
import pytest

from tm_engine import Tape, run_machine


def machine(transitions, *, start="q0", accept=("yes",), reject=("no",)):
    return {
        "states": ["q0", "q1", "yes", "no"],
        "input_alphabet": ["0", "1"],
        "tape_alphabet": ["0", "1", "B", "X"],
        "blank_symbol": "B",
        "start_state": start,
        "accept_states": list(accept),
        "reject_states": list(reject),
        "transitions": transitions,
    }


def rule(state, read, next_state, write, direction):
    return {"current_state": state, "read_symbol": read, "next_state": next_state,
            "write_symbol": write, "direction": direction}


def test_accept_and_trace_are_json_serializable():
    result = run_machine(machine([rule("q0", "1", "yes", "1", "R")]), "1")
    assert result["status"] == "ACCEPT"
    assert result["reason"] == "accept_state"
    assert result["steps"] == 1
    assert result["trace"][0]["step"] == 0
    assert result["trace"][-1]["head"] == 1
    assert result["final_tape"] == ["1", "B"]
    json.dumps(result)


def test_reject_state():
    result = run_machine(machine([rule("q0", "0", "no", "0", "S")]), "0")
    assert (result["status"], result["reason"]) == ("REJECT", "reject_state")


def test_missing_transition_is_project_convention_reject():
    result = run_machine(machine([]), "0")
    assert (result["status"], result["reason"]) == ("REJECT", "missing_transition")
    assert result["steps"] == 0


def test_empty_input_starts_on_blank_and_can_accept():
    result = run_machine(machine([rule("q0", "B", "yes", "B", "S")]), "")
    assert result["status"] == "ACCEPT"
    assert result["final_tape"] == ["B"]
    assert result["trace"][0]["read"] == "B"


def test_right_expansion_and_left_expansion():
    tape = Tape("0", "B")
    tape.move("R")
    assert tape.head_position == 1 and tape.read() == "B"
    tape.move("L")
    assert tape.head_position == 0 and tape.read() == "0"
    tape.move("L")
    assert tape.head_position == 0 and tape.read() == "B"
    assert tape.snapshot() == ["B", "0", "B"]


def test_transition_left_right_and_stay():
    transitions = [rule("q0", "0", "q1", "X", "L"),
                   rule("q1", "B", "q1", "B", "R"),
                   rule("q1", "X", "yes", "X", "S")]
    result = run_machine(machine(transitions), "0")
    assert result["status"] == "ACCEPT"
    assert [r["move"] for r in result["trace"][1:]] == ["L", "R", "S"]
    assert result["head_position"] == 1


def test_step_limit_is_not_rejection_or_acceptance():
    loop = machine([rule("q0", "0", "q0", "0", "S")])
    result = run_machine(loop, "0", max_steps=3)
    assert (result["status"], result["reason"]) == ("STEP_LIMIT", "max_steps")
    assert result["steps"] == 3
    assert len(result["trace"]) == 4


def test_parser_style_tuple_keyed_transition_map_is_supported():
    m = machine({("q0", "1"): {"next_state": "yes", "write_symbol": "1", "direction": "S"}})
    assert run_machine(m, "1")["status"] == "ACCEPT"


def test_duplicate_transition_and_invalid_direction_rejected():
    with pytest.raises(ValueError, match="Duplicate"):
        run_machine(machine([rule("q0", "0", "yes", "0", "S"),
                             rule("q0", "0", "no", "0", "S")]), "0")
    with pytest.raises(ValueError, match="direction"):
        run_machine(machine([rule("q0", "0", "yes", "0", "U")]), "0")


def test_step_limit_must_be_positive_and_states_disjoint():
    with pytest.raises(ValueError):
        run_machine(machine([]), "", max_steps=0)
    with pytest.raises(ValueError, match="overlap"):
        run_machine(machine([], accept=("q0",), reject=("q0",)), "")
