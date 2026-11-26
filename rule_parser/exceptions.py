"""Domain-specific exceptions for Turing Machine rule parsing and validation."""


class RuleParserError(ValueError):
    """Base class for errors raised while parsing transition rules."""

    def __init__(self, message: str, line_number: int | None = None) -> None:
        self.message = message
        self.line_number = line_number
        prefix = f"Line {line_number}: " if line_number is not None else ""
        super().__init__(prefix + message)


class RuleSyntaxError(RuleParserError):
    """A transition rule does not match the documented grammar."""


class InvalidDirectionError(RuleParserError):
    """A transition uses a direction other than L, R, or S."""


class DuplicateTransitionError(RuleParserError):
    """Two rules define the same (current_state, read_symbol) pair."""


class MachineValidationError(ValueError):
    """A machine definition violates the project machine contract."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
