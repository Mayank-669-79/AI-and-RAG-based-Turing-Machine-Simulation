# API Documentation

## 1. API Overview

The API provides endpoints for generating and executing deterministic Turing Machines from supported natural-language conditions.

- Framework: FastAPI
- Data Format: JSON
- API Version: 0.1.0
- Base URL: http://127.0.0.1:8000
- Swagger Documentation: http://127.0.0.1:8000/docs
- ReDoc Documentation: http://127.0.0.1:8000/redoc

## 2. Available Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | /api/health | Check API availability |
| POST | /api/machine/generate | Generate a validated machine |
| POST | /api/machine/run | Generate and execute a machine |

## 3. Health Check

**Endpoint:** GET /api/health

Checks whether the API server is running.

**Response — HTTP 200**

```json
{
  "status": "ok"
}
```

A successful health check does not guarantee that all integration dependencies are available.

## 4. Machine Generation

**Endpoint:** POST /api/machine/generate

Generates and validates a deterministic Turing Machine without executing it.

### Request Parameters

| Parameter | Type | Required | Default |
|---|---|---|---|
| condition | string | Yes | None |
| alphabet | array of strings | No | ["0", "1"] |

### Example Request

```json
{
  "condition": "Accept strings ending with 1",
  "alphabet": ["0", "1"]
}
```

### Successful Response Fields

HTTP Status: 200

| Field | Type | Description |
|---|---|---|
| success | boolean | Request success indicator |
| condition | object | Normalized language condition |
| machine | object | Generated machine definition |
| rules_text | string | Formatted transition rules |
| rag_sources | array | Retrieved reference information |

## 5. Machine Execution

**Endpoint:** POST /api/machine/run

Generates, validates and executes a Turing Machine using the supplied input string.

### Request Parameters

| Parameter | Type | Required | Default |
|---|---|---|---|
| condition | string | Yes | None |
| alphabet | array of strings | No | ["0", "1"] |
| input_string | string | No | Empty string |
| max_steps | integer | No | 1000 |

The max_steps parameter must be between 1 and 100000.

### Example Request

```json
{
  "condition": "Accept strings ending with 1",
  "alphabet": ["0", "1"],
  "input_string": "101",
  "max_steps": 1000
}
```

### Successful Response Fields

HTTP Status: 200

| Field | Description |
|---|---|
| success | Request success indicator |
| condition | Normalized language condition |
| machine | Generated machine definition |
| rules_text | Human-readable transition rules |
| status | Machine execution outcome |
| reason | Reason for execution outcome |
| steps | Number of execution steps |
| final_state | Final machine state |
| final_tape | Final tape contents |
| head_position | Final tape head position |
| trace | Execution history |
| rag_sources | Retrieved reference information |
| explanation | Human-readable execution explanation |

## 6. Execution Outcomes

| Status | Reason | Description |
|---|---|---|
| ACCEPT | accept_state | Machine reached its accept state |
| REJECT | reject_state | Machine reached its reject state |
| REJECT | missing_transition | No valid transition was available |
| STEP_LIMIT | max_steps | Maximum execution steps reached |

ACCEPT, REJECT and STEP_LIMIT are valid execution outcomes and return HTTP 200 when execution completes successfully.

## 7. Execution Trace

The execution trace records the machine's configurations and execution steps.

Trace information includes:

- Step number
- Current state
- Head position
- Read symbol
- Written symbol
- Movement direction
- Tape contents

The frontend uses this information to visualize machine execution.

## 8. Transition Rule Format

Transition rules follow the shared rule parser grammar.

```text
q0, 1 -> q1, 1, R
```

The rule represents:

- Current state: q0
- Read symbol: 1
- Next state: q1
- Write symbol: 1
- Movement direction: R

## 9. Error Response Format

Errors are returned using a standardized JSON structure.

```json
{
  "success": false,
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "Integration dependencies are unavailable.",
    "details": {}
  }
}
```

Ambiguous condition responses additionally include normalized condition information and a clarification question.

## 10. Error Codes

| HTTP Status | Error Code |
|---|---|
| 400 | INVALID_CONDITION |
| 400 | INVALID_ALPHABET |
| 400 | INVALID_INPUT |
| 400 | INVALID_INPUT_SYMBOL |
| 400 | INVALID_STEP_LIMIT |
| 400 | ALPHABET_MISMATCH |
| 404 | NOT_FOUND |
| 405 | METHOD_NOT_ALLOWED |
| 422 | INVALID_REQUEST |
| 422 | AMBIGUOUS_CONDITION |
| 422 | MACHINE_BUILD_ERROR |
| 500 | INTERPRETATION_ERROR |
| 500 | MACHINE_VALIDATION_ERROR |
| 500 | EXECUTION_ERROR |
| 500 | INTERNAL_ERROR |
| 503 | RETRIEVAL_ERROR |
| 503 | SERVICE_UNAVAILABLE |

Request schema validation failures return INVALID_REQUEST with HTTP 422 in the production application.

## 11. Request Validation Rules

- Condition must be a non-empty string.
- Whitespace-only conditions are rejected by the service.
- Alphabet must contain valid, unique, single-character symbols.
- The reserved blank symbol B must not appear in the input alphabet.
- Input strings must contain only permitted alphabet symbols.
- Maximum execution steps must be within the supported range.
- Unexpected request fields are not permitted.
- Ambiguous conditions require clarification.

## 12. CORS Configuration

The production API permits the following local development origins:

- http://localhost:5500
- http://127.0.0.1:5500
- http://localhost:8000
- http://127.0.0.1:8000

Additional deployment origins must be configured before external deployment.

## 13. Running the Production API

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

Production machine endpoints require the actual NLP interpreter, RAG retriever, rule parser and validator.

## 14. Running the Temporary Demo API

```powershell
python -m uvicorn demo_app:app --reload --port 8000
```

The demo application uses controlled mock dependencies for development and testing.

Its mock interpreter generates the ends_with condition for symbol 1. It must not be treated as a complete natural-language interpreter.

The demo may also return different framework-level validation error formats because it does not include all production exception handlers.

## 15. Testing

Run API-specific tests:

```powershell
python -m pytest tests/test_api.py -v
```

Run integration workflow tests:

```powershell
python -m pytest tests/test_integration_workflow.py -v
```

Run the complete test suite:

```powershell
python -m pytest -q
```

Latest confirmed local result: 236 passed.

## 16. Integration Status

The API integration layer is implemented and tested using controlled dependencies.

Actual teammate module integration and production end-to-end verification remain pending.