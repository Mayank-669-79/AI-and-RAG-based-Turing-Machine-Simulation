# Rule Parser and Validator — Member 3 (Mayank Gupta)

This module parses readable deterministic Turing Machine transition rules and validates complete machine definitions before they are passed to the execution engine.

## Responsibilities

- Parse one transition per line using the shared project syntax.
- Ignore blank lines and comments beginning with `#`.
- Preserve line numbers in parser errors.
- Reject malformed rules, invalid directions, and duplicate `(current_state, read_symbol)` keys.
- Validate machine states, alphabets, blank symbol, and transitions.
- Provide a deterministic lookup map for efficient transition selection.

The module does **not** execute a Turing Machine and does not decide ACCEPT or REJECT.

## Folder structure

```text
rule_parser/
├── __init__.py
├── parser.py
├── validator.py
├── models.py
├── exceptions.py
├── README.md
└── tests/
    ├── test_parser.py
    └── test_validator.py
```

## Transition syntax

```text
current_state, read_symbol -> next_state, write_symbol, direction
```

Example:

```text
# Scan right over 0s and 1s
q0, 0 -> q0, 0, R
q0, 1 -> q1, 1, R
q1, 0 -> q_accept, 0, S
```

Rules:

- `#` begins a comment; text after it is ignored.
- Blank lines are ignored.
- State names must be non-empty.
- Read and write symbols must each be exactly one character.
- Direction must be `L`, `R`, or `S`.
- A deterministic machine may define only one transition for each `(current_state, read_symbol)` pair.

## Public interfaces

```python
from rule_parser import parse_rules, validate_machine

transition_map = parse_rules(rule_text)
validated_machine = validate_machine(machine)
```

### `parse_rules(rule_text: str) -> dict`

Returns a dictionary keyed by `(current_state, read_symbol)`. Each value contains `next_state`, `write_symbol`, and `direction`.

Example result:

```python
{
    ("q0", "0"): {
        "next_state": "q0",
        "write_symbol": "0",
        "direction": "R",
    },
    ("q0", "1"): {
        "next_state": "q1",
        "write_symbol": "1",
        "direction": "R",
    },
}
```

### `validate_machine(machine: dict) -> dict`

Accepts the machine dictionary described in the root README. The `transitions` field may be the documented list of transition objects or the lookup map returned by `parse_rules`.

It returns an independent validated copy. The returned object contains:

- `transitions`: normalized list of transition objects.
- `transition_map`: lookup dictionary keyed by `(current_state, read_symbol)`.

Validation checks required fields, declared start/accept/reject/current/next states, input-alphabet inclusion, tape symbols, blank symbol, transition directions, duplicate keys, and accept/reject overlap.

## Exceptions

- `RuleSyntaxError`: malformed rule or invalid symbol width.
- `InvalidDirectionError`: direction is not `L`, `R`, or `S`.
- `DuplicateTransitionError`: repeated deterministic transition key.
- `MachineValidationError`: invalid machine definition.

Parser exceptions expose `line_number` when the error is tied to a source line.

## Example usage

```python
from rule_parser import parse_rules, validate_machine

rules = """
q0, 0 -> q0, 0, R
q0, 1 -> q_accept, 1, S
"""

lookup = parse_rules(rules)

machine = {
    "states": ["q0", "q_accept", "q_reject"],
    "input_alphabet": ["0", "1"],
    "tape_alphabet": ["0", "1", "B"],
    "blank_symbol": "B",
    "start_state": "q0",
    "accept_states": ["q_accept"],
    "reject_states": ["q_reject"],
    "transitions": [
        {
            "current_state": "q0",
            "read_symbol": "0",
            "next_state": "q0",
            "write_symbol": "0",
            "direction": "R",
        },
        {
            "current_state": "q0",
            "read_symbol": "1",
            "next_state": "q_accept",
            "write_symbol": "1",
            "direction": "S",
        },
    ],
}

validated = validate_machine(machine)
print(lookup)
print(validated["transition_map"])
```

## Tests

Run from the repository root (or from the directory containing `rule_parser/`):

```bash
python -m pytest rule_parser/tests -q
```

The tests cover valid rules, comments, blank lines, malformed syntax, line-numbered errors, invalid directions, duplicate rules, machine-state checks, alphabet checks, and accept/reject overlap.

## Dependencies

No third-party runtime dependency is required. The module uses only the Python standard library. `pytest` is required to run the tests and is already listed in the root README's development dependencies.

## Integration notes

- Member 2 (TM engine) can use the parser's `(state, symbol)` lookup map or the validated machine's `transition_map`.
- Member 6 (API integration) should call `parse_rules` and `validate_machine`; do not duplicate parsing or validation logic.
- The parser returns transition values with exactly `next_state`, `write_symbol`, and `direction`, matching the lookup shape in the root README.
- This module does not modify shared root files or other members' folders.
