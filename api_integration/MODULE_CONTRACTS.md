# Module Contracts and Integration Requirements

## 1. Purpose

This document defines the interfaces required to connect independently developed modules to the API integration layer.

All modules must follow compatible input and output formats to ensure successful machine generation and execution.

## 2. Module Responsibilities

| Module | Developer | Responsibility |
|---|---|---|
| Frontend | Abhayraj | User interface and visualization |
| NLP Interpreter | Sarvatha | Natural language interpretation |
| RAG Pipeline | Aditya | Knowledge retrieval |
| Rule Parser | Mayank | Transition parsing and validation |
| TM Engine | Ayusha | Machine execution |
| API Integration | Saakshi | Machine construction and system coordination |

## 3. NLP Interpreter Contract

**Package:** nlp_interpreter

**Required function:**

```python
interpret_condition(text: str) -> dict
```

### Example Input

```text
Accept strings ending with 1
```

### Expected Output

```json
{
  "family": "ends_with",
  "parameters": {
    "symbol": "1"
  },
  "alphabet": ["0", "1"],
  "confidence": 1.0,
  "needs_clarification": false
}
```

### Ambiguous Condition Output

```json
{
  "needs_clarification": true,
  "clarification_question": "Which symbol should the string end with?"
}
```

### Supported Families and Parameters

| Family | Parameters |
|---|---|
| starts_with | symbol |
| ends_with | symbol |
| contains | substring |
| does_not_contain | substring |
| length_parity | parity |
| count_parity | symbol, parity |
| starts_and_ends | start_symbol, end_symbol |
| exact_string | value |
| empty_or_nonempty | mode |

Parity values must be even or odd.

Mode values must be empty or nonempty.

The interpreter must return a mapping containing a supported family and compatible parameters for unambiguous conditions.

## 4. RAG Pipeline Contract

**Package:** rag_pipeline

**Required function:**

```python
retrieve_context(query: str, top_k: int = 4) -> list[dict]
```

### Example Input

```python
retrieve_context(
    "Accept strings ending with 1",
    top_k=4
)
```

### Example Output

```json
[
  {
    "chunk_id": "example_001",
    "text": "Reference information about Turing Machines.",
    "source": "automata_notes.pdf",
    "topic": "Turing Machines",
    "language": "English",
    "content_type": "theory",
    "distance": 0.15
  }
]
```

The returned value must be a list of mappings.

An empty list is permitted.

RAG context is used as reference information and does not directly generate executable machine transitions.

The example metadata is illustrative.

## 5. Machine Builder Contract

**Package:** api_integration.machine_builder

**Required function:**

```python
build_machine(
    normalized_condition,
    retrieved_context=None
) -> dict
```

### Responsibilities

- Validate normalized conditions.
- Select the appropriate machine template.
- Construct deterministic transitions.
- Define initial, accepting and rejecting states.
- Return the generated machine definition.

### Transition Structure

```json
{
  "current_state": "q0",
  "read_symbol": "1",
  "next_state": "q1",
  "write_symbol": "1",
  "direction": "R"
}
```

The reserved blank symbol is B.

Retrieved context does not alter deterministic machine construction in the current implementation.

## 6. Rule Parser Contract

**Package:** rule_parser

**Required function:**

```python
parse_rules(rule_text: str) -> dict
```

### Example Input

```text
q0, 1 -> q1, 1