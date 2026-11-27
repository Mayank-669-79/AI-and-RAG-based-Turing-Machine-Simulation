"""Conservative checks for unclear or unsupported condition language."""

from __future__ import annotations

import re

from .condition_schema import ConditionResult


def clarification_result(
    question: str,
    *,
    alphabet: list[str] | None = None,
    confidence: float = 0.0,
) -> dict:
    """Build a consistent clarification response without inventing a machine."""
    return ConditionResult(
        family=None,
        parameters={},
        alphabet=alphabet or ["0", "1"],
        confidence=confidence,
        needs_clarification=True,
        clarification_question=question,
    ).to_dict()


def detect_ambiguous(text: str) -> str | None:
    """Return a clarification question for common conflicting/underspecified requests."""
    if not text.strip():
        return "Please describe the string condition you want to recognize."
    if re.search(r"\b(?:starts|begins)\b", text) and re.search(r"\b(?:ends|finishes)\b", text) and not re.search(r"\b(?:and|but)\b", text):
        return "Should the condition constrain the beginning, the ending, or both?"
    if re.search(r"\b(?:even|odd)\b", text) and re.search(r"\b(?:even|odd)\b", text):
        matches = re.findall(r"\b(even|odd)\b", text)
        if len(matches) > 1 and matches[0] != matches[-1]:
            return "The condition mentions both even and odd. Which parity should be accepted?"
    if re.search(r"\b(?:alphabet|symbols?)\b", text) and re.search(r"\b(?:not sure|whatever|anything)\b", text):
        return "Which input alphabet should I use? Please list its symbols."
    return None
