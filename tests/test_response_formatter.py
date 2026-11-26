"""Unit and integration tests for API response formatting."""

import json
from copy import deepcopy

import pytest

from api_integration import build_machine
from api_integration.response_formatter import (
    ResponseFormattingError,
    format_clarification_response,
    format_error_response,
    format_generation_response,
    format_rag_sources,
    format_rules_text,
    format_simulation_response,
)
from tm_engine import run_machine


@pytest.fixture
def condition() -> dict:
    """Provide a reusable normalized language condition."""

    return {
        "family": "ends_with",
        "parameters": {"symbol": "1"},
        "alphabet": ["0", "1"],
        "confidence": 1.0,
        "needs_clarification": False,
    }


@pytest.fixture
def machine(condition: dict) -> dict:
    """Provide a deterministic machine for response testing."""

    return build_machine(condition)


@pytest.fixture
def rag_context() -> list[dict]:
    """Provide synthetic retrieval data for isolated testing."""

    return [
        {
            "chunk_id": "test_chunk_001",
            "source": "binary_language_patterns.md",
            "topic": "ends_with",
            "language": "binary",
            "content_type": "construction_example",
            "text": "Track the most recently read symbol.",
            "distance": 0.15,
        }
    ]


def test_rules_text_format(machine: dict) -> None:
    """Verify compatibility with the documented rule grammar."""

    rules = format_rules_text(machine)

    assert "q0, 1 -> q1, 1, R" in rules
    assert "q1, B -> q_accept, B, S" in rules

    assert len(rules.splitlines()) == len(
        machine["transitions"]
    )


@pytest.mark.parametrize(
    "invalid_machine",
    [
        {},
        {"transitions": None},
        {"transitions": {}},
        {"transitions": [{}]},
    ],
)
def test_invalid_machine_rules(invalid_machine: dict) -> None:
    """Reject malformed transition structures."""

    with pytest.raises(ResponseFormattingError):
        format_rules_text(invalid_machine)


def test_rag_source_metadata(rag_context: list[dict]) -> None:
    """Preserve retrieved source metadata."""

    sources = format_rag_sources(rag_context)

    assert sources == rag_context


@pytest.mark.parametrize("context", [None, []])
def test_empty_rag_context(context) -> None:
    """Return no sources when retrieval provides no results."""

    assert format_rag_sources(context) == []


def test_rag_metadata_filtering() -> None:
    """Exclude unknown fields and missing metadata."""

    context = [
        {
            "chunk_id": "test_001",
            "source": "example.md",
            "topic": None,
            "score": 0.95,
            "internal_field": "not exposed",
        }
    ]

    assert format_rag_sources(context) == [
        {
            "chunk_id": "test_001",
            "source": "example.md",
            "score": 0.95,
        }
    ]


def test_invalid_rag_context() -> None:
    """Reject malformed retrieval items."""

    with pytest.raises(ResponseFormattingError):
        format_rag_sources(["invalid"])


def test_generation_response(
    condition: dict,
    machine: dict,
    rag_context: list[dict],
) -> None:
    """Verify the machine generation response structure."""

    response = format_generation_response(
        condition,
        machine,
        rag_context,
    )

    assert response["success"] is True
    assert response["condition"] == condition
    assert response["machine"] == machine
    assert response["rag_sources"] == rag_context
    assert response["rules_text"] == format_rules_text(machine)


@pytest.mark.parametrize(
    "input_string, max_steps, expected_status, expected_reason",
    [
        ("101", 1000, "ACCEPT", "accept_state"),
        ("110", 1000, "REJECT", "reject_state"),
        ("", 1000, "REJECT", "reject_state"),
        ("101010", 2, "STEP_LIMIT", "max_steps"),
    ],
)
def test_simulation_response(
    condition: dict,
    machine: dict,
    input_string: str,
    max_steps: int,
    expected_status: str,
    expected_reason: str,
) -> None:
    """Verify response formatting for actual engine outcomes."""

    result = run_machine(
        machine,
        input_string,
        max_steps=max_steps,
    )

    response = format_simulation_response(
        condition,
        machine,
        result,
    )

    assert response["success"] is True
    assert response["status"] == expected_status
    assert response["reason"] == expected_reason

    for field in (
        "steps",
        "final_state",
        "final_tape",
        "head_position",
        "trace",
    ):
        assert response[field] == result[field]

    assert response["explanation"]
    assert response["rag_sources"] == []


def test_missing_transition_response(
    condition: dict,
    machine: dict,
) -> None:
    """Preserve rejection caused by an undefined transition."""

    incomplete_machine = deepcopy(machine)

    incomplete_machine["transitions"] = [
        transition
        for transition in incomplete_machine["transitions"]
        if not (
            transition["current_state"] == "q0"
            and transition["read_symbol"] == "1"
        )
    ]

    result = run_machine(incomplete_machine, "1")

    response = format_simulation_response(
        condition,
        incomplete_machine,
        result,
    )

    assert response["status"] == "REJECT"
    assert response["reason"] == "missing_transition"


def test_missing_execution_fields(
    condition: dict,
    machine: dict,
) -> None:
    """Reject incomplete execution results."""

    result = run_machine(machine, "101")
    del result["final_state"]

    with pytest.raises(
        ResponseFormattingError,
        match="final_state",
    ):
        format_simulation_response(
            condition,
            machine,
            result,
        )


@pytest.mark.parametrize(
    "status, reason",
    [
        ("UNKNOWN", "accept_state"),
        ("ACCEPT", "max_steps"),
        ("REJECT", "accept_state"),
        ("STEP_LIMIT", "reject_state"),
    ],
)
def test_invalid_execution_outcomes(
    condition: dict,
    machine: dict,
    status: str,
    reason: str,
) -> None:
    """Reject inconsistent execution outcomes."""

    result = run_machine(machine, "101")

    result["status"] = status
    result["reason"] = reason

    with pytest.raises(ResponseFormattingError):
        format_simulation_response(
            condition,
            machine,
            result,
        )


def test_empty_execution_trace(
    condition: dict,
    machine: dict,
) -> None:
    """Reject execution results without computation history."""

    result = run_machine(machine, "101")
    result["trace"] = []

    with pytest.raises(ResponseFormattingError):
        format_simulation_response(
            condition,
            machine,
            result,
        )


def test_error_response() -> None:
    """Verify the shared API error response schema."""

    response = format_error_response(
        code="INVALID_REQUEST",
        message="Invalid input string.",
        details={"symbol": "2"},
    )

    assert response == {
        "success": False,
        "error": {
            "code": "INVALID_REQUEST",
            "message": "Invalid input string.",
            "details": {"symbol": "2"},
        },
    }


def test_error_response_without_details() -> None:
    """Use an empty details object when none is supplied."""

    response = format_error_response(
        "INVALID_REQUEST",
        "Invalid request.",
    )

    assert response["error"]["details"] == {}


def test_clarification_response() -> None:
    """Preserve clarification questions from the interpreter."""

    condition = {
        "needs_clarification": True,
        "clarification_question": "Which symbol should be counted?",
    }

    response = format_clarification_response(condition)

    assert response["success"] is False
    assert response["error"]["code"] == "AMBIGUOUS_CONDITION"
    assert response["condition"]["needs_clarification"] is True

    assert response["clarification_question"] == (
        "Which symbol should be counted?"
    )


@pytest.mark.parametrize(
    "question",
    [None, "", "   "],
)
def test_default_clarification_question(question) -> None:
    """Provide a useful fallback clarification question."""

    response = format_clarification_response(
        {
            "needs_clarification": True,
            "clarification_question": question,
        }
    )

    assert response["clarification_question"] == (
        "Please provide a more specific language condition."
    )


def test_response_is_json_serializable(
    condition: dict,
    machine: dict,
    rag_context: list[dict],
) -> None:
    """Verify compatibility with JSON-based API communication."""

    result = run_machine(machine, "101")

    response = format_simulation_response(
        condition,
        machine,
        result,
        rag_context,
    )

    serialized = json.dumps(response)

    assert json.loads(serialized) == response


def test_response_does_not_mutate_original_data(
    condition: dict,
    machine: dict,
    rag_context: list[dict],
) -> None:
    """Ensure response modifications do not affect source data."""

    result = run_machine(machine, "101")

    original_condition = deepcopy(condition)
    original_machine = deepcopy(machine)
    original_result = deepcopy(result)
    original_context = deepcopy(rag_context)

    response = format_simulation_response(
        condition,
        machine,
        result,
        rag_context,
    )

    response["condition"]["parameters"]["symbol"] = "0"
    response["machine"]["states"].clear()
    response["trace"].clear()
    response["final_tape"].clear()
    response["rag_sources"][0]["source"] = "changed.md"

    assert condition == original_condition
    assert machine == original_machine
    assert result == original_result
    assert rag_context == original_context