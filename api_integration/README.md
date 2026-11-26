# API Integration Module

## 1. Overview

The API Integration module coordinates the components of the AI and RAG-Based Turing Machine Simulation project.

It acts as the connecting layer between the frontend, natural language interpreter, RAG pipeline, machine builder, rule parser, validator and Turing Machine execution engine.

**Developer:** Saakshi Sharma

## 2. Responsibilities

- Receive requests from the frontend.
- Coordinate natural language interpretation.
- Retrieve relevant knowledge through the RAG pipeline.
- Construct deterministic Turing Machines.
- Coordinate rule parsing and machine validation.
- Execute Turing Machines.
- Format execution results and traces.
- Handle invalid requests and integration errors.
- Return structured JSON responses.

## 3. Module Structure

```text
api_integration/
    __init__.py
    machine_builder.py
    response_formatter.py
    service.py
    routes.py
    README.md
    TESTING_REPORT.md
```

### machine_builder.py

Constructs deterministic Turing Machines from normalized language conditions using predefined machine-building templates.

### response_formatter.py

Formats generated machines, execution results, retrieved references, clarification requests and error responses into structured JSON.

### service.py

Coordinates the complete machine generation and simulation workflow through dependency injection.

### routes.py

Defines FastAPI endpoints and manages HTTP responses and integration dependency initialization.

### TESTING_REPORT.md

Records automated testing results, testing coverage, limitations and remaining integration tasks.

## 4. Supported Language Conditions

1. Strings starting with a symbol.
2. Strings ending with a symbol.
3. Strings containing a substring.
4. Strings not containing a substring.
5. Strings with even or odd length.
6. Strings with an even or odd count of a symbol.
7. Strings starting and ending with specified symbols.
8. Exact string matching.
9. Empty strings.
10. Non-empty strings.

## 5. System Workflow

```text
Frontend Request
       |
       v
FastAPI Routes
       |
       v
Machine Service
       |
       v
NLP Interpretation
       |
       v
RAG Context Retrieval
       |
       v
Machine Construction
       |
       v
Rule Parsing and Validation
       |
       v
Machine Execution
       |
       v
Response Formatting
       |
       v
Frontend Response
```

Machine generation requests do not require machine execution.

RAG context provides reference information. Machine transitions are constructed deterministically using supported templates.

## 6. API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | /api/health | Check API health |
| POST | /api/machine/generate | Generate a Turing Machine |
| POST | /api/machine/run | Generate and execute a Turing Machine |

## 7. Technologies

- Python
- FastAPI
- Pydantic
- Uvicorn
- Pytest
- JSON
- REST API
- Dependency Injection

## 8. Testing

Run the complete automated test suite from the project root:

```powershell
python -m pytest -q
```

Latest confirmed testing results:

- Total tests: 236
- Passed: 236
- Failed: 0
- Pass rate: 100%

See TESTING_REPORT.md for testing details and limitations.

## 9. Design Principles

- Modular architecture
- Separation of concerns
- Deterministic machine construction
- Dependency injection
- Structured error handling
- Standardized API responses
- Automated testing
- Maintainability

## 10. Current Implementation Status

The core integration layer, machine builder, API routes and response formatter have been implemented and tested.

Controlled integration testing uses mock implementations for unavailable teammate dependencies.

Final integration with the actual NLP interpreter, RAG retriever, rule parser and validator must be completed by the designated team integration developer.

The temporary demo application is intended for development and testing only.

## 11. Handover

The integration module is designed to support independently developed teammate modules through defined interfaces.

Before production deployment, the team must verify actual module compatibility, complete frontend testing and perform end-to-end testing without mock dependencies.