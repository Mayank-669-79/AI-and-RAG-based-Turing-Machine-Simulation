"""Module-local tests for the interpreter's supported patterns and safeguards."""

import pytest

from nlp_interpreter import interpret_condition


@pytest.mark.parametrize(
    ("text", "family", "parameters"),
    [
        ("The binary string should end with 1", "ends_with", {"symbol": "1"}),
        ("Every accepted word finishes with `0`", "ends_with", {"symbol": "0"}),
        ("The string starts with 1", "starts_with", {"symbol": "1"}),
        ("Words begin with '0'", "starts_with", {"symbol": "0"}),
        ("Accept strings containing substring 101", "contains", {"substring": "101"}),
        ("The word includes `00`", "contains", {"substring": "00"}),
        ("Reject strings that do not contain 11", "does_not_contain", {"substring": "11"}),
        ("Words without substring '010'", "does_not_contain", {"substring": "010"}),
        ("The binary string has even length", "length_parity", {"parity": "even"}),
        ("Accept words with an odd number of symbols", "length_parity", {"parity": "odd"}),
        ("Even number of zeros", "count_parity", {"symbol": "0", "parity": "even"}),
        ("Accept strings with an odd count of ones", "count_parity", {"symbol": "1", "parity": "odd"}),
        ("Start with 1 and end with 0", "starts_and_ends", {"start_symbol": "1", "end_symbol": "0"}),
        ("The string begins with '0' and finishes with '1'", "starts_and_ends", {"start_symbol": "0", "end_symbol": "1"}),
        ("The string is exactly '1010'", "exact_string", {"value": "1010"}),
        ("Accept only the string `01`", "exact_string", {"value": "01"}),
        ("The input string is empty", "empty_or_nonempty", {"value": "empty"}),
        ("Accept non-empty strings", "empty_or_nonempty", {"value": "nonempty"}),
    ],
)
def test_supported_conditions(text, family, parameters):
    result = interpret_condition(text)

    assert result["family"] == family
    assert result["parameters"] == parameters
    assert result["needs_clarification"] is False
    assert result["clarification_question"] is None
    assert result["confidence"] == 1.0


def test_explicit_alphabet_is_preserved():
    result = interpret_condition("strings that end with a", alphabet=["a", "b"])

    assert result["alphabet"] == ["a", "b"]
    assert result["parameters"] == {"symbol": "a"}


def test_parity_words_do_not_leak_into_inferred_alphabet():
    result = interpret_condition("even length")

    assert result["alphabet"] == ["0", "1"]


def test_nonbinary_symbols_require_an_explicit_alphabet():
    result = interpret_condition("strings that end with a")

    assert result["needs_clarification"] is True


@pytest.mark.parametrize(
    "text",
    [
        "The string starts with 1; ends with 0",
        "Accept strings with an even and odd number of zeros",
        "",
        "The string is prime",
    ],
)
def test_unclear_or_unsupported_input_requests_clarification(text):
    result = interpret_condition(text)

    assert result["family"] is None
    assert result["needs_clarification"] is True
    assert result["clarification_question"]


def test_negation_is_not_lost():
    result = interpret_condition("Does not contain '11'")

    assert result["family"] == "does_not_contain"


def test_invalid_explicit_alphabet_is_clarified():
    result = interpret_condition("ends with 1", alphabet=[])

    assert result["needs_clarification"] is True
