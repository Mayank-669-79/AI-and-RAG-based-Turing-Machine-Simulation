# Natural-language condition interpreter

This folder implements Member 4's contribution from the root README. It turns supported English descriptions into the shared normalized condition object. It does not build a machine, execute a simulation, or decide whether an input is accepted.

## Supported families

The deterministic parser recognizes:

| Family | Examples |
| --- | --- |
| `starts_with` | “starts with 1”; “begins with `0`” |
| `ends_with` | “ends with 1”; “the final symbol is `0`”* |
| `contains` | “contains `101`”; “includes substring `00`” |
| `does_not_contain` | “does not contain `11`”; “without substring `00`” |
| `length_parity` | “even length”; “an odd number of symbols” |
| `count_parity` | “even number of zeros”; “odd count of ones” |
| `starts_and_ends` | “starts with 1 and ends with 0” |
| `exact_string` | “is exactly `1010`”; “exactly the string `01`” |
| `empty_or_nonempty` | “the input is empty”; “accept non-empty strings” |

Quoted symbols and substrings can use single quotes, double quotes, or backticks. Common binary forms may be unquoted. Supply an `alphabet` argument to set the alphabet explicitly; otherwise the default is `['0', '1']`, except for an explicitly unary request. The parser does not silently reverse negation or parity. Unrecognized or ambiguous requests return `needs_clarification: true`.

`*` Descriptions of a final symbol should use “ends with” or “suffix” wording for reliable recognition.

## Public interface

```python
from nlp_interpreter import interpret_condition

result = interpret_condition("Accept binary strings with an even number of zeros")
```

Signature: `interpret_condition(text: str, alphabet: Sequence[str] | None = None) -> dict`.

Successful results follow the root contract:

```json
{
  "family": "count_parity",
  "parameters": {"symbol": "0", "parity": "even"},
  "alphabet": ["0", "1"],
  "confidence": 1.0,
  "needs_clarification": false,
  "clarification_question": null
}
```

For clarification, `family` is `null`, `parameters` is empty, and `clarification_question` explains what is missing. Consumers should stop the pipeline when `needs_clarification` is true. The machine builder must only receive a validated supported family.

## Setup and checks

The implementation uses the project's existing Pydantic 2 dependency. From the repository root, run the local module checks with:

```powershell
python -m pytest nlp_interpreter/tests -q
```

No LLM provider is enabled. `llm_adapter.py` defines a provider protocol and a validation boundary for future use; provider output remains data and is never executed.
