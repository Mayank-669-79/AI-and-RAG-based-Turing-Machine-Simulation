import pytest

from rule_parser import (
    DuplicateTransitionError,
    InvalidDirectionError,
    RuleSyntaxError,
    parse_rules,
)


def test_parse_valid_rules_and_lookup_shape():
    parsed = parse_rules("q0, 0 -> q0, 0, R\nq0, 1 -> q1, 1, S")
    assert parsed == {
        ("q0", "0"): {"next_state": "q0", "write_symbol": "0", "direction": "R"},
        ("q0", "1"): {"next_state": "q1", "write_symbol": "1", "direction": "S"},
    }


def test_comments_and_blank_lines_are_ignored():
    parsed = parse_rules("# header\n\n q0, 0 -> q1, 0, L  # inline comment\n")
    assert len(parsed) == 1
    assert parsed[("q0", "0")]["direction"] == "L"


def test_malformed_rule_reports_source_line():
    with pytest.raises(RuleSyntaxError) as error:
        parse_rules("# comment\nq0, 0 -> q1, 0")
    assert error.value.line_number == 2
    assert "Line 2" in str(error.value)


def test_empty_state_is_rejected():
    with pytest.raises(RuleSyntaxError):
        parse_rules(", 0 -> q1, 0, R")


def test_multi_character_symbol_is_rejected():
    with pytest.raises(RuleSyntaxError) as error:
        parse_rules("q0, blank -> q1, 0, R")
    assert error.value.line_number == 1


def test_invalid_direction_is_rejected_with_line_number():
    with pytest.raises(InvalidDirectionError) as error:
        parse_rules("q0, 0 -> q1, 0, UP")
    assert error.value.line_number == 1


def test_duplicate_transition_is_rejected():
    rules = "q0, 0 -> q0, 0, R\nq0, 0 -> q1, 1, L"
    with pytest.raises(DuplicateTransitionError) as error:
        parse_rules(rules)
    assert error.value.line_number == 2


def test_non_string_input_is_rejected():
    with pytest.raises(TypeError):
        parse_rules(None)
