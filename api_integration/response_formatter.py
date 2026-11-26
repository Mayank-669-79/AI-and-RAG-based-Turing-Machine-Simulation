"""Response formatting utilities for the Turing Machine API."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from app.schemas import ApiErrorResponse, ErrorDetail


class ResponseFormattingError(ValueError):
    """Raised when backend data cannot form a valid API response."""


_RESULT_EXPLANATIONS: dict[tuple[str, str], str] = {
    ("ACCEPT", "accept_state"): (
        "The validated machine reached its accept state."
    ),
    ("REJECT", "reject_state"): (
        "The validated machine reached its reject state."
    ),
    ("REJECT", "missing_transition"): (
        "No transition is defined for the current configuration."
    ),
    ("STEP_LIMIT", "max_steps"): (
        "The machine reached the maximum allowed execution steps "
        "without reaching a halting state."
    ),
}


_REQUIRED_RESULT_FIELDS = frozenset(
    {
        "status",
        "reason",
        "steps",
        "final_state",
        "final_tape",
        "head_position",
        "trace",
    }
)


def format_rules_text(machine: Mapping[str, Any]) -> str:
    """Serialize transitions using the shared rule parser grammar."""

    transitions = machine.get("transitions")

    if not isinstance(transitions, list):
        raise ResponseFormattingError(
            "Machine transitions must be provided as a list."
        )

    rules: list[str] = []

    for transition in transitions:
        try:
            current_state = transition["current_state"]
            read_symbol = transition["read_symbol"]
            next_state = transition["next_state"]
            write_symbol = transition["write_symbol"]
            direction = transition["direction"]

        except (KeyError, TypeError) as exc:
            raise ResponseFormattingError(
                "The machine contains an invalid transition."
            ) from exc

        rules.append(
            f"{current_state}, {read_symbol} -> "
            f"{next_state}, {write_symbol}, {direction}"
        )

    return "\n".join(rules)

def format_rag_sources(
    retrieved_context: Sequence[Mapping[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Prepare retrieved knowledge and metadata for the frontend.

    Missing metadata is omitted rather than replaced with
    fabricated source information.
    """

    if retrieved_context is None:
        return []

    sources: list[dict[str, Any]] = []

    allowed_fields = (
    "chunk_id",
    "source",
    "topic",
    "language",
    "content_type",
    "text",
    "distance",
    "score",
)

    for chunk in retrieved_context:
        if not isinstance(chunk, Mapping):
            raise ResponseFormattingError(
                "Retrieved context must contain mapping objects."
            )

        source = {
            field: deepcopy(chunk[field])
            for field in allowed_fields
            if field in chunk and chunk[field] is not None
        }

        if source:
            sources.append(source)

    return sources


def format_generation_response(
    normalized_condition: Mapping[str, Any],
    machine: Mapping[str, Any],
    retrieved_context: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a successful machine generation response."""

    return {
        "success": True,
        "condition": deepcopy(dict(normalized_condition)),
        "machine": deepcopy(dict(machine)),
        "rules_text": format_rules_text(machine),
        "rag_sources": format_rag_sources(retrieved_context),
    }


def format_simulation_response(
    normalized_condition: Mapping[str, Any],
    machine: Mapping[str, Any],
    execution_result: Mapping[str, Any],
    retrieved_context: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a simulation response using actual engine results.

    Execution status, tape contents and trace are preserved.
    The formatter never independently determines acceptance
    or rejection.
    """

    missing_fields = _REQUIRED_RESULT_FIELDS.difference(
        execution_result
    )

    if missing_fields:
        raise ResponseFormattingError(
            "Execution result is missing required fields: "
            + ", ".join(sorted(missing_fields))
        )

    status = execution_result["status"]
    reason = execution_result["reason"]

    if not isinstance(status, str) or not isinstance(reason, str):
        raise ResponseFormattingError(
            "Execution status and reason must be strings."
        )

    explanation = _RESULT_EXPLANATIONS.get((status, reason))

    if explanation is None:
        raise ResponseFormattingError(
            f"Invalid execution outcome: {status!r}, {reason!r}."
        )

    trace = execution_result["trace"]

    if not isinstance(trace, list) or not trace:
        raise ResponseFormattingError(
            "Execution result must contain a populated trace."
        )

    return {
        "success": True,
        "condition": deepcopy(dict(normalized_condition)),
        "machine": deepcopy(dict(machine)),
        "rules_text": format_rules_text(machine),
        "status": status,
        "reason": reason,
        "steps": execution_result["steps"],
        "final_state": execution_result["final_state"],
        "final_tape": deepcopy(execution_result["final_tape"]),
        "head_position": execution_result["head_position"],
        "trace": deepcopy(trace),
        "rag_sources": format_rag_sources(retrieved_context),
        "explanation": explanation,
    }


def format_error_response(
    code: str,
    message: str,
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Create an error response using the shared Pydantic schema."""

    response = ApiErrorResponse(
        error=ErrorDetail(
            code=code,
            message=message,
            details=dict(details) if details is not None else {},
        )
    )

    return response.model_dump(mode="json")


def format_clarification_response(
    normalized_condition: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a structured response for an ambiguous condition."""

    question = normalized_condition.get("clarification_question")

    if not isinstance(question, str) or not question.strip():
        question = (
            "Please provide a more specific language condition."
        )

    response = format_error_response(
        code="AMBIGUOUS_CONDITION",
        message="The condition requires clarification.",
        details={
            "clarification_question": question,
        },
    )

    condition = deepcopy(dict(normalized_condition))
    condition["needs_clarification"] = True
    condition["clarification_question"] = question

    response["condition"] = condition
    response["clarification_question"] = question

    return response