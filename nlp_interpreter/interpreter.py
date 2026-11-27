"""Deterministic phrase-pattern interpreter for supported string languages."""

from __future__ import annotations

import re
from collections.abc import Sequence

from .ambiguity import clarification_result, detect_ambiguous
from .condition_schema import ConditionResult

_QUOTED = r"(?:'([^']*)'|\"([^\"]*)\"|`([^`]*)`)"
_PARITY = {"even": "even", "odd": "odd"}


def _quoted_value(match: re.Match[str]) -> str:
    return next((group for group in match.groups() if group is not None), "")


def _alphabet_from_text(text: str, supplied: Sequence[str] | None) -> tuple[list[str] | None, bool]:
    """Return alphabet and whether it was explicitly supplied."""
    if supplied is not None:
        symbols = list(supplied)
        if not symbols or any(not isinstance(item, str) or len(item) != 1 for item in symbols) or len(set(symbols)) != len(symbols):
            return None, True
        return symbols, True
    match = re.search(r"\b(?:alphabet|over)\s*(?:is|of|=|:)?\s*[\[{(]([^\]})]+)[\]})]", text, re.I)
    if match:
        symbols = re.findall(r"[A-Za-z0-9]|[^\s,|]", match.group(1))
        symbols = list(dict.fromkeys(symbols))
        if symbols:
            return symbols, True
        return None, True
    if re.search(r"\b(?:unary|one-symbol alphabet)\b", text, re.I):
        return ["1"], False
    return ["0", "1"], False


def _extract_symbol(text: str, kind: str) -> str | None:
    quoted = re.search(rf"\b{kind}\b\s*(?:of|is|with|=|to)?\s*{_QUOTED}", text, re.I)
    if quoted:
        value = _quoted_value(quoted)
        return value if len(value) == 1 else None
    # Conventional forms: ends with 1, starts in 0, number of zeros.
    if kind == "zero":
        return "0"
    if kind == "one":
        return "1"
    return None


def interpret_condition(text: str, alphabet: Sequence[str] | None = None) -> dict:
    """Return a normalized condition object or a clarification response.

    The interpreter recognizes the documented condition families using
    deterministic patterns. It never computes ACCEPT/REJECT.

    Args:
        text: User's natural-language condition.
        alphabet: Optional explicit sequence of one-character input symbols.
    """
    if not isinstance(text, str):
        return clarification_result("Please provide the condition as text.")
    normalized = " ".join(text.strip().lower().split())
    symbols, alphabet_was_explicit = _alphabet_from_text(normalized, alphabet)
    if symbols is None:
        return clarification_result("Please provide a non-empty alphabet of unique one-character symbols.")
    if not normalized:
        return clarification_result("Please describe the string condition you want to recognize.", alphabet=symbols)
    ambiguity = detect_ambiguous(normalized)
    if ambiguity:
        return clarification_result(ambiguity, alphabet=symbols)

    family: str | None = None
    parameters: dict[str, str] = {}
    confidence = 1.0

    # Extract an exact-string request before substring patterns.
    exact_patterns = (
        rf"\b(?:is|equals?|exactly|equal to)\s*{_QUOTED}",
        rf"\b(?:only|exactly)\s+the\s+string\s*{_QUOTED}",
    )
    exact_match = next((m for pattern in exact_patterns if (m := re.search(pattern, normalized, re.I))), None)
    if exact_match and re.search(r"\b(?:exactly|exact string|only the string|is exactly|equals?)\b", normalized):
        family, parameters = "exact_string", {"value": _quoted_value(exact_match)}

    if family is None:
        emptiness = re.search(r"\b(non[- ]empty|nonempty|empty)\b", normalized)
        if emptiness and re.search(r"\b(?:strings?|inputs?)\b", normalized):
            family = "empty_or_nonempty"
            value = "empty" if emptiness.group(1) == "empty" else "nonempty"
            if re.search(r"\bnot\s+empty\b", normalized):
                value = "nonempty"
            parameters = {"value": value}

    if family is None:
        parity = re.search(r"\b(even|odd)\b", normalized)
        if parity and re.search(r"\b(?:length|number of symbols|symbols|characters)\b", normalized):
            family, parameters = "length_parity", {"parity": _PARITY[parity.group(1)]}
        elif parity:
            count_match = re.search(r"\b(?:number|count)\s+of\s+(zeros?|0s?|ones?|1s?)\b|\b(even|odd)\s+(zeros?|0s?|ones?|1s?)\b", normalized)
            if count_match:
                token = (count_match.group(1) or count_match.group(3)).rstrip("s")
                symbol = "0" if token in {"zero", "0"} else "1"
                family, parameters = "count_parity", {"symbol": symbol, "parity": parity.group(1)}

    if family is None:
        start_form = r"(?:start(?:s|ing)?\s+(?:with|in)|begin(?:s|ning)?\s+with)"
        end_form = r"(?:end(?:s|ing)?\s+(?:with|in)|finish(?:es|ing)?\s+with)"
        start_end = re.search(rf"\b{start_form}\s*{_QUOTED}.*?\b{end_form}\s*{_QUOTED}", normalized, re.I)
        # unquoted common form: starts with 1 and ends with 0
        if start_end:
            start, end = _quoted_value_from_groups(start_end, 0), _quoted_value_from_groups(start_end, 3)
            family, parameters = "starts_and_ends", {"start_symbol": start, "end_symbol": end}
        else:
            plain = re.search(rf"\b{start_form}\s+([a-z0-9])\b.*?\b{end_form}\s+([a-z0-9])\b", normalized)
            if plain:
                family, parameters = "starts_and_ends", {"start_symbol": plain.group(1), "end_symbol": plain.group(2)}

    if family is None:
        negated = re.search(rf"\b(?:does not|doesn't|do not|don't|without|not)\s+(?:contain|include|have)?\s*(?:the\s+)?(?:substring\s+)?{_QUOTED}", normalized, re.I)
        positive = re.search(rf"\b(?:contain(?:s|ing)?|include(?:s|ing)?|has|have)\s*(?:the\s+)?(?:substring\s+)?{_QUOTED}", normalized, re.I)
        if negated:
            family, parameters = "does_not_contain", {"substring": _quoted_value(negated)}
        elif positive:
            family, parameters = "contains", {"substring": _quoted_value(positive)}
        else:
            # Common unquoted examples are restricted to binary substrings.
            negated_plain = re.search(r"\b(?:does not|doesn't|do not|don't|without|not)\s+(?:contain|include)?\s*(?:the\s+)?(?:substring\s+)?([01]+)\b", normalized)
            positive_plain = re.search(r"\b(?:contain(?:s|ing)?|include(?:s|ing)?|has|have)\s*(?:the\s+)?(?:substring\s+)?([01]+)\b", normalized)
            if negated_plain:
                family, parameters = "does_not_contain", {"substring": negated_plain.group(1)}
            elif positive_plain:
                family, parameters = "contains", {"substring": positive_plain.group(1)}

    if family is None:
        for direction, forms in (("starts_with", r"start(?:s|ing)?\s+(?:with|in)|begin(?:s|ning)?\s+with|prefix(?:ed)?\s+by"),
                                 ("ends_with", r"end(?:s|ing)?\s+(?:with|in)|finish(?:es|ing)?\s+with|suffix(?:ed)?\s+by")):
            match = re.search(rf"\b(?:{forms})\s*{_QUOTED}", normalized, re.I)
            if match:
                symbol = _quoted_value(match)
                if len(symbol) == 1:
                    family, parameters = direction, {"symbol": symbol}
                    break
            plain = re.search(rf"\b(?:{forms})\s+([a-z0-9])\b", normalized, re.I)
            if plain:
                family, parameters = direction, {"symbol": plain.group(1)}
                break

    if family is None and re.search(r"\b(?:exactly|is|equals?)\b", normalized):
        quoted = re.search(_QUOTED, normalized)
        if quoted and re.search(r"\bstring\b", normalized):
            family, parameters = "exact_string", {"value": _quoted_value(quoted)}

    if family is None:
        reason = "I couldn't match that condition to a supported pattern. Please rephrase it using a documented condition, or clarify the intended rule."
        return clarification_result(reason, alphabet=symbols)

    if family in {"starts_with", "ends_with"} and len(parameters["symbol"]) != 1:
        return clarification_result("Please specify one symbol for the beginning or ending condition.", alphabet=symbols)
    if family in {"contains", "does_not_contain"} and not parameters["substring"]:
        return clarification_result("Please specify a non-empty substring to include or exclude.", alphabet=symbols)
    if family in {"starts_and_ends"} and (len(parameters["start_symbol"]) != 1 or len(parameters["end_symbol"]) != 1):
        return clarification_result("Please specify one symbol for both the beginning and ending.", alphabet=symbols)

    # Keep the alphabet semantically sound: do not infer symbols from words
    # like "even", and do not silently expand a declared alphabet.
    symbol_keys = {"symbol", "substring", "start_symbol", "end_symbol", "value"}
    if family == "empty_or_nonempty":
        symbol_keys = set()
    mentioned = set("".join(parameters[key] for key in symbol_keys if key in parameters))
    outside = mentioned.difference(symbols)
    if outside and alphabet_was_explicit:
        return clarification_result(
            f"The condition uses symbol(s) {', '.join(sorted(outside))} outside the supplied alphabet. Please correct the condition or alphabet.",
            alphabet=symbols,
        )
    if outside and not alphabet_was_explicit:
        return clarification_result(
            "The condition uses symbols outside the default binary alphabet. Please provide the complete input alphabet.",
            alphabet=symbols,
        )
    result = ConditionResult(
        family=family,
        parameters=parameters,
        alphabet=symbols,
        confidence=confidence,
        needs_clarification=False,
        clarification_question=None,
    )
    return result.to_dict()


def _quoted_value_from_groups(match: re.Match[str], start: int) -> str:
    """Get one quoted capture from an expression with two quoted groups."""
    return next((group for group in match.groups()[start : start + 3] if group is not None), "")
