"""Typed contract for normalized language conditions."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ConditionFamily = Literal[
    "starts_with",
    "ends_with",
    "contains",
    "does_not_contain",
    "length_parity",
    "count_parity",
    "starts_and_ends",
    "exact_string",
    "empty_or_nonempty",
]


class ConditionResult(BaseModel):
    """Validated output consumed by the machine-builder integration layer."""

    model_config = ConfigDict(extra="forbid")

    family: ConditionFamily | None
    parameters: dict[str, Any] = Field(default_factory=dict)
    alphabet: list[str] = Field(default_factory=lambda: ["0", "1"])
    confidence: float = Field(ge=0.0, le=1.0)
    needs_clarification: bool
    clarification_question: str | None = None

    @field_validator("alphabet")
    @classmethod
    def validate_alphabet(cls, alphabet: list[str]) -> list[str]:
        if not alphabet or any(not isinstance(symbol, str) or len(symbol) != 1 for symbol in alphabet):
            raise ValueError("alphabet must contain one-character symbols")
        if len(set(alphabet)) != len(alphabet):
            raise ValueError("alphabet symbols must be unique")
        return alphabet

    @model_validator(mode="after")
    def clarification_consistency(self) -> "ConditionResult":
        if self.needs_clarification and not self.clarification_question:
            raise ValueError("clarification_question is required when clarification is needed")
        if not self.needs_clarification and self.family is None:
            raise ValueError("a supported family is required when clarification is not needed")
        return self

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-compatible data using the shared project contract."""
        return self.model_dump(mode="json")
