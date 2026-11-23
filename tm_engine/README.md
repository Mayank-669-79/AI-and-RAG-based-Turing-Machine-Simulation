# Turing Machine Execution Engine

`tm_engine` is a deterministic, dependency-free Python executor for the formal TM model used by the project. It owns tape behavior, a single transition, full execution, and JSON-friendly trace records.

## Quick start

```python
from tm_engine import run_machine

machine = {
    "states": ["q0", "accept", "reject"],
    "input_alphabet": ["0", "1"],
    "tape_alphabet": ["0", "1", "B"],
    "blank_symbol": "B",
    "start_state": "q0",
    "accept_states": ["accept"],
    "reject_states": ["reject"],
    "transitions": [
        {"current_state": "q0", "read_symbol": "1", "next_state": "accept",
         "write_symbol": "1", "direction": "R"}
    ],
}
result = run_machine(machine, "1", max_steps=100)
print(result["status"])  # ACCEPT
```

The transition input may be either a list of dictionaries as above, or a mapping keyed by `(state, read_symbol)` whose values contain `next_state`, `write_symbol`, and `direction`. This accepts the tuple-keyed map returned by the project's rule parser. Directions are `L`, `R`, or `S` (case-insensitive). Duplicate list transitions and malformed rules raise `ValueError` rather than being silently overwritten.

## Public API

- `Tape(input_string="", blank_symbol="B")`: tape with `read()`, `write(symbol)`, `move(direction)`, and `snapshot()` methods. Empty input starts on one blank cell. Moving past either allocated boundary adds a blank cell.
- `execute_step(machine, state, tape, transitions=None)`: runs one transition and returns the new configuration. Missing transition raises `KeyError`.
- `run_machine(machine, input_string, max_steps=1000)`: runs to a halting state, a missing transition, or the step limit.

The machine requires a non-empty `start_state`; `blank_symbol` defaults to `B`. `accept_states` and `reject_states` default to empty collections and must not overlap. Full alphabet/state validation belongs to `rule_parser`; this module performs checks needed to execute and rejects malformed transition data.

## Result and trace

The result is JSON-serializable:

```json
{
  "status": "ACCEPT",
  "reason": "accept_state",
  "steps": 1,
  "final_state": "accept",
  "final_tape": ["1", "B"],
  "head_position": 1,
  "trace": [
    {"step": 0, "state": "q0", "head": 0, "read": "1", "write": null, "move": null, "tape": ["1"]},
    {"step": 1, "state": "accept", "head": 1, "read": "B", "write": "1", "move": "R", "tape": ["1", "B"]}
  ]
}
```

Trace has the initial configuration at step 0 and one record after each transition. The `read` in each record is the symbol under the head in that recorded configuration; `write` and `move` describe the transition that led to it (null for the initial configuration). Tape snapshots are independent copies.

Statuses and reasons:

| Status | Reason | Meaning |
|---|---|---|
| `ACCEPT` | `accept_state` | Entered a declared accepting state. |
| `REJECT` | `reject_state` | Entered a declared rejecting state. |
| `REJECT` | `missing_transition` | No rule is defined for the state and scanned symbol (project convention). |
| `STEP_LIMIT` | `max_steps` | Reached the configured transition count without halting. Never interpreted as accept or reject. |

`max_steps` must be a positive integer. The returned `steps` counts transitions, not trace records. Results are deterministic for the same machine and input.

## Tests

From the repository root, run `python -m pytest tm_engine/tests -q` (pytest is a development dependency). The module tests cover left/right/stay movement, empty input, accept/reject/missing rules, tape expansion, deterministic traces, and the step limit.
