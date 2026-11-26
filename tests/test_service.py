"""Tests for the machine integration service."""

import json
from unittest.mock import Mock

import pytest

from api_integration.service import MachineService
from tm_engine import run_machine

def mock_interpreter(condition):
    return {
        "family": "ends_with",
        "parameters": {"symbol": "1"},
        "alphabet": ["0", "1"],
        "confidence": 1.0,
        "needs_clarification": False,
    }

def mock_retriever(query, top_k=4):
    return [
        {
            "chunk_id": "test_001",
            "source": "automata.md",
            "topic": "ends_with",
            "text": "Track the last symbol.",
            "distance": 0.12,
        }
    ]

def mock_parser(rules_text):
    transitions = {}

    for line in rules_text.splitlines():
        left, right = line.split("->")

        current_state, read_symbol = [
            item.strip() for item in left.split(",")
        ]

        next_state, write_symbol, direction = [
            item.strip() for item in right.split(",")
        ]

        transitions[(current_state, read_symbol)] = {
            "next_state": next_state,
            "write_symbol": write_symbol,
            "direction": direction,
        }

    return transitions

def mock_validator(machine):
    return machine

@pytest.fixture
def service():
    return MachineService(
        interpreter=Mock(side_effect=mock_interpreter),
        retriever=Mock(side_effect=mock_retriever),
        parser=Mock(side_effect=mock_parser),
        validator=Mock(side_effect=mock_validator),
        runner=Mock(side_effect=run_machine),
    )

def test_generate_machine(service):
    response = service.generate_machine(
        "Accept strings ending with 1"
    )

    assert response["success"] is True
    assert response["machine"]["transitions"]
    assert response["rules_text"]
    assert response["rag_sources"]

    service.interpreter.assert_called_once()
    service.retriever.assert_called_once()
    service.parser.assert_called_once()
    service.validator.assert_called_once()
    service.runner.assert_not_called()

@pytest.mark.parametrize(
    "input_string, expected_status",
    [
        ("101", "ACCEPT"),
        ("110", "REJECT"),
        ("111", "ACCEPT"),
        ("000", "REJECT"),
        ("", "REJECT"),
    ],
)
def test_simulate_machine(
    service,
    input_string,
    expected_status,
):
    response = service.simulate_machine(
        "Accept strings ending with 1",
        input_string,
    )

    assert response["success"] is True
    assert response["status"] == expected_status
    assert response["trace"]

    service.runner.assert_called_once()

def test_step_limit(service):
    response = service.simulate_machine(
        "Accept strings ending with 1",
        "101010",
        max_steps=2,
    )

    assert response["success"] is True
    assert response["status"] == "STEP_LIMIT"
    assert response["reason"] == "max_steps"

@pytest.mark.parametrize("condition", ["", "   ", None])
def test_invalid_condition(service, condition):
    response = service.generate_machine(condition)

    assert response["success"] is False
    assert response["error"]["code"] == "INVALID_CONDITION"

    service.interpreter.assert_not_called()

def test_ambiguous_condition(service):
    service.interpreter.side_effect = None

    service.interpreter.return_value = {
        "needs_clarification": True,
        "clarification_question": "Which symbol?",
    }

    response = service.generate_machine(
        "Accept strings ending with something"
    )

    assert response["success"] is False
    assert response["error"]["code"] == "AMBIGUOUS_CONDITION"
    assert response["clarification_question"] == "Which symbol?"

    service.retriever.assert_not_called()
    service.parser.assert_not_called()
    service.runner.assert_not_called()

def test_invalid_input_symbol(service):
    response = service.simulate_machine(
        "Accept strings ending with 1",
        "1021",
    )

    assert response["success"] is False

    assert response["error"]["code"] == (
        "INVALID_INPUT_SYMBOL"
    )

    assert response["error"]["details"]["invalid_symbols"] == [
        "2"
    ]

    service.runner.assert_not_called()

@pytest.mark.parametrize("input_string", [None, 101, []])
def test_invalid_input_type(service, input_string):
    response = service.simulate_machine(
        "Accept strings ending with 1",
        input_string,
    )

    assert response["success"] is False
    assert response["error"]["code"] == "INVALID_INPUT"

    service.runner.assert_not_called()

@pytest.mark.parametrize(
    "max_steps",
    [0, -1, 100001, 1.5, True],
)
def test_invalid_step_limit(service, max_steps):
    response = service.simulate_machine(
        "Accept strings ending with 1",
        "101",
        max_steps=max_steps,
    )

    assert response["success"] is False

    assert response["error"]["code"] == (
        "INVALID_STEP_LIMIT"
    )

    service.runner.assert_not_called()

def test_alphabet_mismatch(service):
    response = service.generate_machine(
        "Accept strings ending with 1",
        alphabet=["a", "b"],
    )

    assert response["success"] is False
    assert response["error"]["code"] == "ALPHABET_MISMATCH"

def test_interpreter_failure(service):
    service.interpreter.side_effect = RuntimeError(
        "Interpreter unavailable"
    )

    response = service.generate_machine("Test condition")

    assert response["success"] is False
    assert response["error"]["code"] == "INTERPRETATION_ERROR"

def test_invalid_interpreter_response(service):
    service.interpreter.side_effect = None
    service.interpreter.return_value = None

    response = service.generate_machine("Test condition")

    assert response["success"] is False
    assert response["error"]["code"] == "INTERPRETATION_ERROR"

def test_retrieval_failure(service):
    service.retriever.side_effect = RuntimeError(
        "Vector database unavailable"
    )

    response = service.generate_machine("Test condition")

    assert response["success"] is False
    assert response["error"]["code"] == "RETRIEVAL_ERROR"

    service.parser.assert_not_called()

def test_invalid_retrieval_response(service):
    service.retriever.side_effect = None
    service.retriever.return_value = "invalid"

    response = service.generate_machine("Test condition")

    assert response["success"] is False
    assert response["error"]["code"] == "RETRIEVAL_ERROR"

def test_empty_retrieval_results(service):
    service.retriever.side_effect = None
    service.retriever.return_value = []

    response = service.generate_machine("Test condition")

    assert response["success"] is True
    assert response["rag_sources"] == []

def test_machine_build_failure(service):
    service.interpreter.side_effect = None

    service.interpreter.return_value = {
        "family": "unsupported_family",
        "parameters": {},
        "alphabet": ["0", "1"],
        "needs_clarification": False,
    }

    response = service.generate_machine("Test condition")

    assert response["success"] is False
    assert response["error"]["code"] == "MACHINE_BUILD_ERROR"

    service.parser.assert_not_called()

def test_parser_failure(service):
    service.parser.side_effect = ValueError("Invalid rules")

    response = service.generate_machine("Test condition")

    assert response["success"] is False

    assert response["error"]["code"] == (
        "MACHINE_VALIDATION_ERROR"
    )

    service.validator.assert_not_called()

def test_validator_failure(service):
    service.validator.side_effect = ValueError(
        "Invalid machine"
    )

    response = service.simulate_machine(
        "Test condition",
        "101",
    )

    assert response["success"] is False

    assert response["error"]["code"] == (
        "MACHINE_VALIDATION_ERROR"
    )

    service.runner.assert_not_called()

def test_invalid_validator_response(service):
    service.validator.side_effect = None
    service.validator.return_value = None

    response = service.generate_machine("Test condition")

    assert response["success"] is False

    assert response["error"]["code"] == (
        "MACHINE_VALIDATION_ERROR"
    )

def test_execution_failure(service):
    service.runner.side_effect = RuntimeError(
        "Execution failed"
    )

    response = service.simulate_machine(
        "Test condition",
        "101",
    )

    assert response["success"] is False
    assert response["error"]["code"] == "EXECUTION_ERROR"

def test_generation_json_serialization(service):
    response = service.generate_machine("Test condition")

    assert response["success"] is True
    assert json.loads(json.dumps(response)) == response

def test_simulation_json_serialization(service):
    response = service.simulate_machine(
        "Test condition",
        "101",
    )

    assert response["success"] is True
    assert json.loads(json.dumps(response)) == response

def test_complete_workflow_order(service):
    calls = Mock()

    calls.attach_mock(service.interpreter, "interpret")
    calls.attach_mock(service.retriever, "retrieve")
    calls.attach_mock(service.parser, "parse")
    calls.attach_mock(service.validator, "validate")
    calls.attach_mock(service.runner, "run")

    response = service.simulate_machine(
        "Test condition",
        "101",
    )

    assert response["success"] is True

    assert [
        call[0] for call in calls.mock_calls
    ] == [
        "interpret",
        "retrieve",
        "parse",
        "validate",
        "run",
    ]


def test_alphabet_order_independence(service):
    response = service.generate_machine(
        "Accept strings ending with 1", alphabet=["1", "0"]
    )
    assert response["success"] is True
    assert response["condition"]["alphabet"] == ["1", "0"]


@pytest.mark.parametrize(
    "alphabet", [[], ["0", "0"], ["0", "B"], ["01", "1"], ["", "1"], [0, 1], "01"]
)
def test_invalid_alphabet(service, alphabet):
    response = service.generate_machine(
        "Accept strings ending with 1", alphabet=alphabet
    )
    assert response["success"] is False
    assert response["error"]["code"] == "INVALID_ALPHABET"
    service.retriever.assert_not_called()
    service.runner.assert_not_called()


def test_invalid_interpreted_alphabet(service):
    service.interpreter.side_effect = None
    service.interpreter.return_value = {
        "family": "ends_with",
        "parameters": {"symbol": "1"},
        "alphabet": ["0", "0"],
        "needs_clarification": False,
    }
    response = service.generate_machine("Accept strings ending with 1")
    assert response["success"] is False
    assert response["error"]["code"] == "INVALID_ALPHABET"


@pytest.mark.parametrize("stage", ["parser", "validator"])
@pytest.mark.parametrize("change", ["remove", "add", "modify"])
def test_transition_consistency(service, stage, change):
    def alter(transitions):
        key = next(iter(transitions))
        if change == "remove":
            del transitions[key]
        elif change == "add":
            transitions[("unexpected", "0")] = dict(transitions[key])
        else:
            transitions[key]["direction"] = "L"
        return transitions

    if stage == "parser":
        service.parser.side_effect = lambda rules: alter(mock_parser(rules))
    else:
        def altered_validator(machine):
            machine["transitions"] = alter(machine["transitions"])
            return machine
        service.validator.side_effect = altered_validator

    response = service.simulate_machine("Accept strings ending with 1", "101")
    assert response["success"] is False
    assert response["error"]["code"] == "MACHINE_VALIDATION_ERROR"
    service.runner.assert_not_called()
    if stage == "parser":
        service.validator.assert_not_called()
