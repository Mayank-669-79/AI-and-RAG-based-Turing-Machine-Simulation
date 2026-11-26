"""Coordinate machine generation and simulation workflows."""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from copy import deepcopy
from typing import Any

from api_integration.machine_builder import (
    MachineBuildError,
    build_machine,
)

from api_integration.response_formatter import (
    format_clarification_response,
    format_error_response,
    format_generation_response,
    format_rules_text,
    format_simulation_response,
)

from tm_engine import run_machine
from tm_engine.engine import transition_lookup


logger = logging.getLogger(__name__)


class ServiceError(Exception):
    """Represent a controlled integration service failure."""

    def __init__(
        self,
        code: str,
        message: str,
        details: dict | None = None,
    ):
        super().__init__(message)

        self.code = code
        self.message = message
        self.details = details or {}


def validate_alphabet(alphabet):
    if not isinstance(alphabet, (list, tuple)) or not alphabet:
        raise ServiceError("INVALID_ALPHABET", "The alphabet must contain at least one symbol.")
    if any(not isinstance(symbol, str) or len(symbol) != 1 for symbol in alphabet):
        raise ServiceError("INVALID_ALPHABET", "Each alphabet symbol must be a single character.")
    if len(set(alphabet)) != len(alphabet) or "B" in alphabet:
        raise ServiceError("INVALID_ALPHABET", "Duplicate symbols and the reserved blank B are not allowed.")
    return list(alphabet)


class MachineService:
    """Connect interpretation, retrieval, validation and execution."""

    def __init__(
        self,
        interpreter: Callable,
        retriever: Callable,
        parser: Callable,
        validator: Callable,
        runner: Callable = run_machine,
    ):
        self.interpreter = interpreter
        self.retriever = retriever
        self.parser = parser
        self.validator = validator
        self.runner = runner

    def prepare_machine(
        self,
        condition: str,
        alphabet: list[str] | None = None,
    ) -> dict[str, Any]:
        """Interpret a condition and construct a validated machine."""

        if not isinstance(condition, str) or not condition.strip():
            raise ServiceError(
                "INVALID_CONDITION",
                "A non-empty language condition is required.",
            )

        condition = condition.strip()

        # Interpret the natural language condition.
        try:
            normalized = self.interpreter(condition)

        except Exception as exc:
            logger.exception("Condition interpretation failed.")

            raise ServiceError(
                "INTERPRETATION_ERROR",
                "The language condition could not be interpreted.",
            ) from exc

        if not isinstance(normalized, Mapping):
            raise ServiceError(
                "INTERPRETATION_ERROR",
                "The interpreter returned an invalid response.",
            )

        normalized = deepcopy(dict(normalized))

        # Stop if the condition needs clarification.
        if normalized.get("needs_clarification"):
            return format_clarification_response(normalized)

        interpreted = normalized.get("alphabet")
        if interpreted is not None:
            interpreted = validate_alphabet(interpreted)
        if alphabet is not None:
            requested = validate_alphabet(alphabet)
            if interpreted is not None and set(interpreted) != set(requested):
                raise ServiceError("ALPHABET_MISMATCH", "The interpreted and requested alphabets differ.", {"requested": requested, "interpreted": interpreted})
            normalized["alphabet"] = requested
        else:
            normalized["alphabet"] = interpreted if interpreted is not None else ["0", "1"]

        # Retrieve relevant automata knowledge.
        try:
            context = self.retriever(condition, top_k=4)

        except Exception as exc:
            logger.exception("Knowledge retrieval failed.")

            raise ServiceError(
                "RETRIEVAL_ERROR",
                "Relevant automata knowledge could not be retrieved.",
            ) from exc

        if not isinstance(context, list) or any(
            not isinstance(chunk, Mapping)
            for chunk in context
        ):
            raise ServiceError(
                "RETRIEVAL_ERROR",
                "The retriever returned an invalid response.",
            )

        # Construct the deterministic machine.
        try:
            machine = build_machine(normalized, context)

        except MachineBuildError as exc:
            raise ServiceError(
                "MACHINE_BUILD_ERROR",
                str(exc),
            ) from exc

        # Parse and validate the generated transition rules.
        try:
            rules_text = format_rules_text(machine)

            parsed_transitions = self.parser(rules_text)

            expected_transitions = transition_lookup(machine)
            if transition_lookup({"transitions": parsed_transitions}) != expected_transitions:
                raise ValueError("Parsed transitions differ from generated rules.")

            machine_for_validation = deepcopy(machine)

            machine_for_validation["transitions"] = (
                parsed_transitions
            )

            validated_machine = self.validator(
                machine_for_validation
            )

            if not isinstance(validated_machine, Mapping):
                raise ValueError(
                    "Validator must return a machine definition."
                )

            if transition_lookup(validated_machine) != expected_transitions:
                raise ValueError("Validated transitions differ from generated rules.")

        except Exception as exc:
            logger.exception("Machine validation failed.")

            raise ServiceError(
                "MACHINE_VALIDATION_ERROR",
                "The generated machine failed rule validation.",
            ) from exc

        # Keep the JSON-compatible and executable machines separate.
        return {
            "success": True,
            "condition": normalized,
            "machine": machine,
            "validated_machine": validated_machine,
            "rag_sources": context,
        }

    def generate_machine(
        self,
        condition: str,
        alphabet: list[str] | None = None,
    ) -> dict[str, Any]:
        """Generate a validated machine without running it."""

        try:
            prepared = self.prepare_machine(
                condition,
                alphabet,
            )

            if not prepared["success"]:
                return prepared

            return format_generation_response(
                prepared["condition"],
                prepared["machine"],
                prepared["rag_sources"],
            )

        except ServiceError as exc:
            return format_error_response(
                exc.code,
                exc.message,
                exc.details,
            )

        except Exception:
            logger.exception("Unexpected machine generation error.")

            return format_error_response(
                "INTERNAL_ERROR",
                "An unexpected machine generation error occurred.",
            )

    def simulate_machine(
        self,
        condition: str,
        input_string: str = "",
        alphabet: list[str] | None = None,
        max_steps: int = 1000,
    ) -> dict[str, Any]:
        """Generate, validate and execute a Turing Machine."""

        try:
            if not isinstance(input_string, str):
                raise ServiceError(
                    "INVALID_INPUT",
                    "The input must be a string.",
                )

            if (
                type(max_steps) is not int
                or not 1 <= max_steps <= 100000
            ):
                raise ServiceError(
                    "INVALID_STEP_LIMIT",
                    "The step limit must be between 1 and 100000.",
                )

            prepared = self.prepare_machine(
                condition,
                alphabet,
            )

            if not prepared["success"]:
                return prepared

            # Verify that the input uses the machine alphabet.
            allowed_symbols = set(
                prepared["condition"]["alphabet"]
            )

            invalid_symbols = sorted(
                set(input_string) - allowed_symbols
            )

            if invalid_symbols:
                raise ServiceError(
                    "INVALID_INPUT_SYMBOL",
                    "The input contains symbols outside the alphabet.",
                    {
                        "invalid_symbols": invalid_symbols,
                        "alphabet": sorted(allowed_symbols),
                    },
                )

            # Execute the validated machine.
            try:
                result = self.runner(
                    prepared["validated_machine"],
                    input_string,
                    max_steps=max_steps,
                )

            except Exception as exc:
                logger.exception("Machine execution failed.")

                raise ServiceError(
                    "EXECUTION_ERROR",
                    "The Turing Machine could not be executed.",
                ) from exc

            return format_simulation_response(
                prepared["condition"],
                prepared["machine"],
                result,
                prepared["rag_sources"],
            )

        except ServiceError as exc:
            return format_error_response(
                exc.code,
                exc.message,
                exc.details,
            )

        except Exception:
            logger.exception("Unexpected simulation error.")

            return format_error_response(
                "INTERNAL_ERROR",
                "An unexpected simulation error occurred.",
            )