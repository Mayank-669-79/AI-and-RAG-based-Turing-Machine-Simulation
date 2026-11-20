# AI-Powered Natural Language Turing Machine Simulator

> **Project type:** Automata Theory / Theory of Computation / AI\
> **Primary language:** Python\
> **Frontend:** HTML, CSS, JavaScript\
> **Backend:** Python + FastAPI\
> **RAG:** Embeddings + vector database + curated automata knowledge
> base\
> **Team size:** 6 contributors

------------------------------------------------------------------------

## 1. Project overview

Build an interactive Turing Machine (TM) language acceptor in which a
user describes a language condition in natural language, supplies an
input string, and receives an **ACCEPT** or **REJECT** result with a
step-by-step simulation.

Example conditions:

-   "The binary string should end with 1."
-   "Accept strings containing an even number of zeros."
-   "The string must start with 1 and end with 0."
-   "Accept strings that contain the substring 101."
-   "The length of the binary string should be even."
-   "Reject strings containing 11."

The system must translate the condition into a formal, deterministic
Turing Machine specification, validate it, and execute it. The user
should be able to inspect the tape, read/write head, current state,
transition applied, and computation history.

### Core design principle

**RAG and language interpretation help construct the machine; the
deterministic TM engine decides acceptance.**

Do not ask an LLM to directly return ACCEPT/REJECT. Do not let retrieved
text execute as code. The final decision must be produced by the
simulator executing a validated machine.

### Scope and honest limitations

"Any condition" is an aspirational interface, not a claim that every
possible natural-language condition can be compiled automatically.
Natural language can be ambiguous, and arbitrary language-membership
problems are not necessarily decidable.

The first release must support a documented set of conditions over
binary strings (`{0,1}`), with optional unary (`{1}`) examples.
Unsupported or ambiguous conditions must produce a clear
clarification/unsupported-condition message rather than a fabricated
machine.

Initial supported condition families:

1.  Starts with a symbol.
2.  Ends with a symbol.
3.  Contains a substring.
4.  Does not contain a substring.
5.  Has even/odd length.
6.  Has an even/odd number of `0`s.
7.  Has an even/odd number of `1`s.
8.  Starts with one symbol and ends with another.
9.  Is exactly a specified string.
10. Is empty / non-empty, where the selected alphabet and semantics
    permit it.

Add new condition families through documented compiler templates and
tests.

------------------------------------------------------------------------

## 2. End-to-end workflow

1.  **User input:** User enters a natural-language condition and an
    input string.
2.  **Input normalization:** Trim whitespace where appropriate; preserve
    the actual input symbols. Determine or confirm the alphabet.
3.  **Condition interpretation:** Extract a structured representation
    such as `{"family":"ends_with","symbol":"1","alphabet":["0","1"]}`.
4.  **Ambiguity check:** If the condition or alphabet is unclear, ask
    the user to clarify. Do not guess silently.
5.  **RAG retrieval:** Retrieve relevant automata theory notes,
    construction examples, transition patterns, and edge-case
    explanations.
6.  **Machine construction:** A deterministic compiler/template layer
    creates a structured TM specification. An LLM may assist with
    interpretation if configured, but its output must be
    schema-validated and checked against supported templates.
7.  **Rule parsing and validation:** Convert transitions into the
    engine's internal representation; reject malformed, duplicate,
    conflicting, or invalid transitions.
8.  **Simulation:** Initialize the tape and execute one transition at a
    time.
9.  **Halting:** Stop on an accept state, reject state, missing
    transition (defined as rejection by project convention), or
    maximum-step safety limit.
10. **Result:** Display ACCEPT / REJECT / INVALID CONDITION / STEP
    LIMIT, plus a trace and explanation.
11. **Learning panel:** Show which RAG sources were retrieved and why
    they were relevant. Clearly label retrieved material as reference
    material, not proof of execution.

------------------------------------------------------------------------

## 3. Architecture

``` text
                         USER
                           |
            Natural-language condition + input
                           |
                    FRONTEND (JS)
                           |
                     FastAPI backend
                           |
                NLP CONDITION INTERPRETER
                           |
              Structured condition / clarification
                           |
                 RAG RETRIEVAL PIPELINE
          (knowledge base + embeddings + vector DB)
                           |
               TM CONSTRUCTION / COMPILER
                           |
                RULE PARSER & VALIDATOR
                           |
                 TM EXECUTION ENGINE
                           |
                 ACCEPT / REJECT / ERROR
                           |
            Trace JSON returned to the frontend
                           |
        Tape visualization + states + explanation
```

### Recommended technology choices

  -------------------------------------------------------------------------
  Layer                   Recommended technology    Purpose
  ----------------------- ------------------------- -----------------------
  Frontend                HTML, CSS, JavaScript     User interface and tape
                                                    visualization

  Backend/API             Python, FastAPI, Pydantic Connect modules and
                                                    expose endpoints

  NLP                     Python; deterministic     Interpret condition
                          patterns first, optional  
                          LLM adapter               

  RAG chunking            Python                    Split curated knowledge
                                                    into retrievable chunks

  Embeddings              `sentence-transformers`   Convert knowledge and
                                                    queries to vectors

  Vector store            ChromaDB                  Store and retrieve
                                                    relevant chunks

  TM construction         Python templates/compiler Produce formal machine
                                                    specifications

  Rule parser             Python                    Parse and validate
                                                    transition rules

  TM engine               Python                    Execute machine
                                                    deterministically

  Testing                 pytest                    Unit and integration
                                                    tests
  -------------------------------------------------------------------------

Keep the LLM provider optional and isolated behind an adapter. The
project must still run in a deterministic demo mode without an API key.

------------------------------------------------------------------------

## 4. GitHub repository structure

**This structure is the contract for the whole team.** Each contributor
owns exactly one of the six top-level contribution folders. The
integration owner creates and maintains root-level files. Do not rename
folders or public interfaces without team agreement.

``` text
natural-language-tm-simulator/
│
├── README.md
├── .gitignore
├── requirements.txt
├── .env.example
├── pyproject.toml
│
├── app/
│   ├── main.py
│   ├── config.py
│   └── schemas.py
│
├── frontend/                  # MEMBER 1
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   ├── app.js
│   │   ├── api.js
│   │   ├── tape.js
│   │   └── visualization.js
│   └── README.md
│
├── tm_engine/                 # MEMBER 2
│   ├── __init__.py
│   ├── engine.py
│   ├── tape.py
│   ├── runner.py
│   ├── trace.py
│   └── README.md
│
├── rule_parser/               # MEMBER 3 — MAYANK
│   ├── __init__.py
│   ├── parser.py
│   ├── validator.py
│   ├── models.py
│   ├── exceptions.py
│   └── README.md
│
├── nlp_interpreter/           # MEMBER 4
│   ├── __init__.py
│   ├── interpreter.py
│   ├── condition_schema.py
│   ├── ambiguity.py
│   ├── llm_adapter.py
│   └── README.md
│
├── rag_pipeline/              # MEMBER 5
│   ├── __init__.py
│   ├── ingest.py
│   ├── chunker.py
│   ├── embedder.py
│   ├── retriever.py
│   ├── store.py
│   ├── knowledge_base/
│   │   ├── tm_basics.md
│   │   ├── transition_rules.md
│   │   ├── binary_language_patterns.md
│   │   └── examples/
│   │       ├── ends_with_one.md
│   │       ├── even_zeros.md
│   │       └── contains_substring.md
│   └── README.md
│
├── api_integration/            # MEMBER 6
│   ├── __init__.py
│   ├── routes.py
│   ├── service.py
│   ├── machine_builder.py
│   ├── response_formatter.py
│   └── README.md
│
├── tests/                      # Integration owner creates; everyone contributes tests
│   ├── test_parser.py
│   ├── test_validator.py
│   ├── test_engine.py
│   ├── test_interpreter.py
│   ├── test_rag.py
│   └── test_api.py
│
├── data/
│   └── .gitkeep
│
└── docs/
    ├── architecture.md
    ├── api_contract.md
    ├── supported_conditions.md
    └── demo_cases.md
```

### Folder ownership rule

-   Member 1 uploads/maintains only `frontend/`.
-   Member 2 uploads/maintains only `tm_engine/`.
-   Member 3 uploads/maintains only `rule_parser/`.
-   Member 4 uploads/maintains only `nlp_interpreter/`.
-   Member 5 uploads/maintains only `rag_pipeline/`.
-   Member 6 uploads/maintains only `api_integration/`.

The integration owner (Member 6, unless the team agrees otherwise)
creates root-level files and coordinates integration. Root files are
shared infrastructure, not a seventh contribution folder. The team must
agree who owns root changes before merging.

**Important:** Each member must upload the complete contents of their
assigned folder, including its own `README.md`, imports, and tests where
applicable. Do not upload a second copy of the entire project. Do not
commit virtual environments, API keys, local vector databases, caches,
or datasets that are not explicitly approved.

------------------------------------------------------------------------

## 5. Team responsibilities and exact deliverables

### MEMBER 1 --- Frontend and visualization

**Folder:** `frontend/`\
**Main language:** HTML, CSS, JavaScript

Build a browser interface that:

1.  Accepts a natural-language condition.
2.  Accepts an input string.
3.  Optionally lets the user select/confirm the alphabet.
4.  Has buttons for Generate Machine, Run, Step, Pause, Reset.
5.  Displays ACCEPT / REJECT / error clearly.
6.  Displays tape cells, current head position, current state, and step
    number.
7.  Displays transition history in a readable table.
8.  Displays the machine's states and transition rules.
9.  Displays retrieved RAG references in a separate panel.
10. Shows clarification messages when the backend reports ambiguity.

Required files:

-   `index.html`: semantic page structure.
-   `css/style.css`: responsive styling.
-   `js/app.js`: event handlers and UI state.
-   `js/api.js`: fetch calls to the backend only.
-   `js/tape.js`: tape-cell rendering.
-   `js/visualization.js`: state, trace, and result rendering.
-   `README.md`: setup and UI notes.

Frontend rules:

-   Do not implement a second independent TM execution engine in
    JavaScript.
-   The Python backend is the source of truth for machine execution.
-   JavaScript may animate the trace returned by Python.
-   Do not hardcode generated transitions or acceptance results.
-   Use the API contract in `docs/api_contract.md`.
-   Backend base URL should be configurable, with local development
    default documented.

Acceptance criteria:

-   A user can submit a condition and string.
-   The UI handles loading, success, validation errors, and server
    errors.
-   Step mode displays one trace step at a time.
-   Run mode plays through the returned trace.
-   Reset returns to the initial trace state.
-   UI remains usable on a laptop and mobile-sized screen.

### MEMBER 2 --- Turing Machine execution engine

**Folder:** `tm_engine/`\
**Language:** Python

Implement the formal deterministic TM executor.

Recommended machine model:

``` python
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
            "read_symbol": "1",
            "next_state": "q_accept",
            "write_symbol": "1",
            "direction": "R"
        }
    ]
}
```

The example above is only a schema illustration, not a complete machine
for a language.

Required files:

-   `tape.py`: tape storage, read, write, head movement, blank
    expansion.
-   `engine.py`: one-step transition execution.
-   `runner.py`: repeated execution, halt detection, maximum-step guard.
-   `trace.py`: structured execution history.
-   `__init__.py`: public exports.
-   `README.md`: engine usage and design.

Formal transition:

\[ `\delta`{=tex}(q,a)=(p,b,D) \]

where `q` is current state, `a` is read symbol, `p` is next state, `b`
is written symbol, and `D` is `L`, `R`, or `S`.

Required behavior:

1.  Initialize tape with the input and blank cells.
2.  Place head at the first input cell (index 0).
3.  Read the current symbol.
4.  Find the transition using `(current_state, read_symbol)`.
5.  Write the specified symbol.
6.  Move head left, right, or stay.
7.  Change state.
8.  Append a trace record.
9.  Stop when an accept/reject state is reached.
10. If no transition exists, halt as REJECT with reason
    `missing_transition` (project convention).
11. Stop at configurable `max_steps` and report `STEP_LIMIT`, not
    ACCEPT.
12. Handle empty input and movement beyond currently allocated tape
    boundaries.
13. Never silently treat a step-limit result as rejection or acceptance.

Suggested public interface:

``` python
def run_machine(machine: dict, input_string: str, max_steps: int = 1000) -> dict:
    """Return final status, final configuration, and full trace."""
```

Suggested output:

``` python
{
    "status": "ACCEPT",
    "reason": "accept_state",
    "steps": 4,
    "final_state": "q_accept",
    "final_tape": ["1", "0", "1", "B"],
    "head_position": 3,
    "trace": [
        {
            "step": 0,
            "state": "q0",
            "head": 0,
            "read": "1",
            "write": None,
            "move": None,
            "tape": ["1", "0", "1", "B"]
        }
    ]
}
```

The exact trace schema must be agreed with Member 1 and Member 6 before
implementation. Include both the initial configuration and each
resulting configuration. Use JSON-serializable values.

Acceptance criteria:

-   Unit tests cover left/right/stay movement.
-   Tests cover empty input.
-   Tests cover accept and reject states.
-   Tests cover missing transitions.
-   Tests cover tape expansion and negative head movement.
-   Tests cover maximum-step protection.
-   Same machine and input always produce the same result.

### MEMBER 3 --- Rule Parser and Validator (MAYANK)

**Folder:** `rule_parser/`\
**Language:** Python

This module converts human-readable transition rules into a validated
machine transition map. Preserve the existing project's rule-parser
concept: parse each rule, detect syntax errors with line numbers, detect
duplicate `(state, read_symbol)` keys, and create an efficient lookup
map. The existing JavaScript prototype used a rule format similar to
`q0, 1 -> q1, 0, R`; this project standardizes that readable format for
the Python backend.

Supported text syntax:

``` text
# Example transition rules
q0, 0 -> q0, 0, R
q0, 1 -> q1, 1, R
q1, 0 -> q_accept, 0, S
```

Grammar:

``` text
current_state, read_symbol -> next_state, write_symbol, direction
```

-   `#` starts a comment.
-   Blank lines are ignored.
-   `direction` must be `L`, `R`, or `S`.
-   State names must be non-empty.
-   Symbols must be one character in the initial implementation.
-   The parser must preserve the source line number for errors.

Required files:

-   `parser.py`: parse text rules into structured transitions.
-   `validator.py`: validate transitions against declared states and
    alphabets.
-   `models.py`: transition/machine data models or typed structures.
-   `exceptions.py`: clear parser and validation exceptions.
-   `__init__.py`: public exports.
-   `README.md`: syntax, examples, and usage.

Required public functions:

``` python
def parse_rules(rule_text: str) -> dict:
    """Parse rules and return a transition map keyed by (state, symbol)."""

def validate_machine(machine: dict) -> dict:
    """Validate machine definition; return validated machine or raise a clear error."""
```

Suggested internal map:

``` python
{
    ("q0", "0"): {
        "next_state": "q0",
        "write_symbol": "0",
        "direction": "R"
    },
    ("q0", "1"): {
        "next_state": "q1",
        "write_symbol": "1",
        "direction": "R"
    }
}
```

Validation requirements:

1.  Reject malformed lines and report the exact line number.
2.  Reject invalid directions.
3.  Reject duplicate `(current_state, read_symbol)` transitions for a
    deterministic TM.
4.  Check that the start state is declared.
5.  Check that accept/reject states are declared.
6.  Check that current and next states are declared.
7.  Check that read symbols belong to the tape alphabet.
8.  Check that write symbols belong to the tape alphabet.
9.  Check that input alphabet is a subset of tape alphabet.
10. Check that the blank symbol belongs to tape alphabet.
11. Reject overlap between accept and reject states.
12. Return useful errors; do not silently discard invalid rules.

**Important interface agreement:** Member 2's engine should consume the
same transition representation returned by this module. Member 6 must
call the public functions, not duplicate parser logic.

Acceptance criteria:

-   Tests for valid rules, comments, and blank lines.
-   Tests for malformed syntax and line-numbered errors.
-   Tests for duplicate transitions.
-   Tests for invalid directions and undeclared states.
-   Tests for symbols outside the tape alphabet.
-   Tests for invalid start/accept/reject states.

### MEMBER 4 --- Natural-language condition interpreter

**Folder:** `nlp_interpreter/`\
**Language:** Python

Convert a user's English condition into a normalized, structured
condition object. This is not the simulator. It must not decide the
final acceptance result.

Examples:

Input:

``` text
The binary string should end with 1
```

Output:

``` json
{
  "family": "ends_with",
  "parameters": {"symbol": "1"},
  "alphabet": ["0", "1"],
  "confidence": 1.0,
  "needs_clarification": false
}
```

Input:

``` text
Accept strings with an even number of zeros
```

Output:

``` json
{
  "family": "count_parity",
  "parameters": {"symbol": "0", "parity": "even"},
  "alphabet": ["0", "1"],
  "confidence": 1.0,
  "needs_clarification": false
}
```

Required files:

-   `interpreter.py`: main interpretation entry point.
-   `condition_schema.py`: allowed families and Pydantic/typed schema.
-   `ambiguity.py`: clarification and unsupported-condition checks.
-   `llm_adapter.py`: optional LLM provider interface; no
    provider-specific code in the main interpreter.
-   `README.md`: supported phrases and examples.

Required public function:

``` python
def interpret_condition(text: str) -> dict:
    """Return normalized condition, clarification status, and explanation."""
```

Recommended initial implementation:

1.  Normalize case and whitespace.
2.  Use deterministic phrase patterns for supported families.
3.  Extract symbols, substrings, parity, and alphabet.
4.  Return a structured condition object.
5.  If deterministic parsing cannot confidently classify the request,
    return a clarification/unsupported response.
6.  Optionally use an LLM adapter to propose a structured object.
7.  Validate all LLM output against the condition schema and supported
    family list.
8.  Never execute code or transitions returned by an LLM.
9.  Do not silently convert "does not contain" into "contains" or
    confuse even and odd.

The interpreter must distinguish: - `ends_with` vs `starts_with` -
`contains` vs `does_not_contain` - `even` vs `odd` - `number_of_zeros`
vs `number_of_ones` - exact string vs substring - user-specified
alphabet vs inferred alphabet

Acceptance criteria:

-   At least two natural-language paraphrases per supported family.
-   Tests for ambiguous requests.
-   Tests for negation and parity.
-   Tests for unsupported requests.
-   Stable JSON output matching the shared schema.

### MEMBER 5 --- RAG pipeline and automata knowledge base

**Folder:** `rag_pipeline/`\
**Language:** Python

Implement Retrieval-Augmented Generation (RAG) for retrieving relevant
Automata Theory knowledge and machine-construction examples.

The RAG system should help answer questions such as: - Which
construction pattern is relevant to "ends with 1"? - What states are
needed to track parity? - What does a transition tuple mean? - What edge
cases should be tested for a contains-substring machine? - Why does a
particular construction accept or reject a sample?

#### RAG workflow

``` text
Curated Markdown knowledge files
             |
          Chunking
             |
       Metadata tagging
             |
       Embedding model
             |
       ChromaDB vector store
             |
 User condition / normalized condition
             |
       Query embedding
             |
   Similarity retrieval (top-k)
             |
 Relevant chunks + metadata + source IDs
             |
  Context supplied to construction/explanation layer
```

Required files:

-   `knowledge_base/`: curated source notes and examples.
-   `chunker.py`: split source documents into useful chunks.
-   `embedder.py`: embedding model wrapper.
-   `store.py`: ChromaDB create/load/upsert functions.
-   `ingest.py`: ingest knowledge files and metadata.
-   `retriever.py`: query and return top-k relevant chunks.
-   `README.md`: setup, ingestion, retrieval, and evaluation.

Use a small, reliable knowledge base written by the team. Suggested
sources: 1. Team-written notes explaining formal TM definitions. 2.
Team-written notes explaining transition rules and halting. 3. Correct,
tested examples for each supported condition family. 4. Edge cases and
common mistakes. 5. A glossary of states, alphabet, tape, head,
transition function, and language acceptor.

Each knowledge chunk should have metadata such as:

``` json
{
  "source": "binary_language_patterns.md",
  "topic": "ends_with",
  "language": "binary",
  "content_type": "construction_example"
}
```

Suggested retrieval function:

``` python
def retrieve_context(query: str, top_k: int = 4) -> list[dict]:
    """Return relevant text chunks with source and similarity metadata."""
```

Each returned item should include: - `text` - `source` - `topic` if
known - `score` or distance if supported - stable chunk ID

RAG implementation rules:

1.  Ingest knowledge files through a repeatable script.
2.  Do not commit a generated local ChromaDB database unless the team
    specifically chooses that approach.
3.  Add a `.gitignore` rule for local vector-store data.
4.  Store source metadata for explainability.
5.  Do not use arbitrary internet text as trusted transition rules.
6.  Retrieval results are reference material, not executable code.
7.  If retrieval is weak or irrelevant, return that fact rather than
    pretending a match exists.
8.  Do not let retrieved content override the user's actual condition.
9.  The machine builder must still validate its generated specification.
10. Document how to rebuild the vector store from committed knowledge
    files.

**How RAG fits the project:** The knowledge base can contain verified
construction patterns. Retrieval returns relevant patterns to the
machine builder, which selects a supported compiler template and fills
its parameters. For example, a request about an even number of zeros
retrieves the parity-tracking construction notes. The compiler then
creates the actual machine. This is a practical, demonstrable RAG
pipeline without relying on hallucinated transition rules.

Acceptance criteria:

-   Ingestion works from a clean checkout.
-   Retrieval returns relevant source chunks for at least five test
    queries.
-   Results include source metadata.
-   Tests check relevant vs irrelevant queries.
-   README documents embedding model, vector DB, chunk size/overlap,
    top-k, and rebuild command.
-   The project can run in deterministic mode without a paid API.

### MEMBER 6 --- API, machine builder, and integration

**Folder:** `api_integration/`\
**Language:** Python

Connect the interpreter, RAG, parser, and engine. This module is the
orchestration layer; it should not reimplement their internals.

Required files:

-   `routes.py`: API route handlers or router.
-   `service.py`: orchestration workflow.
-   `machine_builder.py`: map normalized condition + retrieved
    construction knowledge to a machine definition.
-   `response_formatter.py`: consistent API responses.
-   `README.md`: API flow and integration notes.

Recommended workflow in `service.py`:

``` text
interpret_condition(condition_text)
        |
if clarification needed -> return clarification response
        |
retrieve_context(normalized condition)
        |
build_machine(normalized condition, retrieved context)
        |
validate_machine(machine)
        |
run_machine(machine, input_string)
        |
format response with result + trace + RAG sources
```

The machine builder must use explicit, tested templates for the
supported condition families. Do not ask an LLM to invent arbitrary
transitions. If an LLM proposes a machine, treat it as untrusted
candidate data and validate it; only supported, tested constructions
should be enabled in the first release.

Required API endpoints:

**POST `/api/machine/generate`**

Request:

``` json
{
  "condition": "The binary string should end with 1",
  "alphabet": ["0", "1"]
}
```

Response:

``` json
{
  "success": true,
  "condition": {
    "family": "ends_with",
    "parameters": {"symbol": "1"},
    "alphabet": ["0", "1"]
  },
  "machine": {
    "start_state": "q0",
    "accept_states": ["q_accept"],
    "reject_states": ["q_reject"],
    "transitions": []
  },
  "rules_text": "..."
}
```

**POST `/api/machine/run`**

Request:

``` json
{
  "condition": "The binary string should end with 1",
  "input_string": "101",
  "alphabet": ["0", "1"],
  "max_steps": 1000
}
```

Response:

``` json
{
  "success": true,
  "status": "ACCEPT",
  "reason": "accept_state",
  "steps": 4,
  "final_state": "q_accept",
  "final_tape": ["1", "0", "1", "B"],
  "head_position": 3,
  "trace": [],
  "rag_sources": [
    {
      "source": "ends_with_one.md",
      "topic": "ends_with"
    }
  ],
  "explanation": "The validated machine reached its accept state."
}
```

The example response is illustrative. A real trace must be populated by
the engine. Do not return a fabricated trace or an incomplete machine as
if it were executable.

**POST `/api/machine/step`** (optional for server-driven stepping)

Request:

``` json
{
  "machine": {},
  "input_string": "101",
  "step_number": 2
}
```

This endpoint is optional. A simpler first implementation returns the
full trace from `/run`, and JavaScript animates it locally.

**GET `/api/health`**

Response:

``` json
{"status": "ok"}
```

Error responses must be consistent:

``` json
{
  "success": false,
  "error": {
    "code": "UNSUPPORTED_CONDITION",
    "message": "This condition is not supported yet.",
    "details": {}
  }
}
```

Suggested error codes: - `INVALID_REQUEST` - `INVALID_ALPHABET` -
`AMBIGUOUS_CONDITION` - `UNSUPPORTED_CONDITION` -
`MACHINE_VALIDATION_ERROR` - `SIMULATION_STEP_LIMIT` - `INTERNAL_ERROR`

Acceptance criteria:

-   API connects all five other modules through their public interfaces.
-   End-to-end test works for at least five condition families.
-   Invalid conditions return helpful errors.
-   API never reports ACCEPT/REJECT without running the engine.
-   RAG sources are included in the response.
-   CORS is configured for local frontend development.

------------------------------------------------------------------------

## 6. Shared data contracts --- do not change casually

All members must use these shared concepts. Member 6 should create
`app/schemas.py` with Pydantic models based on these contracts. Each
module may use its own internal classes, but conversion at module
boundaries must follow this schema.

### 6.1 Normalized condition

``` json
{
  "family": "ends_with",
  "parameters": {"symbol": "1"},
  "alphabet": ["0", "1"],
  "confidence": 1.0,
  "needs_clarification": false,
  "clarification_question": null
}
```

Initial `family` values:

``` text
starts_with
ends_with
contains
does_not_contain
length_parity
count_parity
starts_and_ends
exact_string
empty_or_nonempty
```

Parameter examples:

``` json
{"family":"length_parity","parameters":{"parity":"even"}}
{"family":"count_parity","parameters":{"symbol":"0","parity":"odd"}}
{"family":"contains","parameters":{"substring":"101"}}
{"family":"starts_and_ends","parameters":{"start_symbol":"1","end_symbol":"0"}}
{"family":"exact_string","parameters":{"value":"1010"}}
```

### 6.2 Machine definition

``` json
{
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
      "direction": "R"
    }
  ]
}
```

This is a schema example only; the transition list is intentionally not
a complete machine. The builder must return complete, tested transitions
for the selected family.

### 6.3 Simulation result

``` json
{
  "status": "ACCEPT",
  "reason": "accept_state",
  "steps": 4,
  "final_state": "q_accept",
  "final_tape": ["1", "0", "1", "B"],
  "head_position": 3,
  "trace": []
}
```

Allowed statuses:

``` text
ACCEPT
REJECT
STEP_LIMIT
INVALID_MACHINE
```

`INVALID_CONDITION` and `NEEDS_CLARIFICATION` belong to the
request/orchestration response, not the TM execution status.

### 6.4 Trace record

``` json
{
  "step": 1,
  "current_state": "q0",
  "head_position": 0,
  "read_symbol": "1",
  "write_symbol": "1",
  "direction": "R",
  "next_state": "q1",
  "tape": ["1", "0", "1", "B"]
}
```

Agree on whether `tape` is recorded before or after the transition.
Recommended: record the resulting configuration after each transition
and include a separate initial configuration at step 0.

------------------------------------------------------------------------

## 7. RAG: what exactly must be demonstrated?

The teacher should be able to see a genuine retrieval pipeline, not
merely a hardcoded list of examples.

Your demonstration should show:

1.  Knowledge documents stored in `rag_pipeline/knowledge_base/`.
2.  Documents split into chunks.
3.  Chunks embedded with a named embedding model.
4.  Embeddings stored in ChromaDB.
5.  User condition converted into a retrieval query.
6.  Top-k relevant chunks retrieved.
7.  Retrieved source names and content shown in the UI/API.
8.  Retrieved context passed to the construction/explanation layer.
9.  The final machine independently validated and executed.

### Suggested RAG configuration

Start with a simple configuration and tune only after it works:

-   Embedding model: `sentence-transformers/all-MiniLM-L6-v2`.
-   Vector database: ChromaDB local persistent client.
-   Chunk size: approximately 400--700 words (or equivalent token-based
    chunking).
-   Chunk overlap: approximately 50--100 words.
-   Retrieval: top-k = 4.
-   Metadata: source file, topic, condition family, content type.
-   Knowledge source: team-authored, verified Markdown files.

These are starting settings, not guaranteed optimal values. Record them
in the RAG README.

### Suggested demo

Query:

``` text
Accept a binary string if it has an even number of zeros.
```

Show: - Interpreter output: `family=count_parity`, `symbol=0`,
`parity=even`. - Retrieved chunks: parity tracking and even/odd state
construction. - Machine builder output: complete transition table. -
Parser validation: passed. - Engine trace: every read/write/move/state
transition. - Final status for `10100`: calculated by the engine. -
Source panel: which knowledge-base documents informed construction.

Also test a paraphrase such as "the number of 0s must be divisible by
two" and an irrelevant query. Retrieval should be evaluated rather than
assumed correct.

------------------------------------------------------------------------

## 8. Root files and environment setup

These files are maintained by the integration owner.

### `requirements.txt`

Start with:

``` text
fastapi
uvicorn[standard]
pydantic
python-dotenv
chromadb
sentence-transformers
pytest
httpx
```

Add optional LLM SDKs only if the team actually uses them. Pin tested
versions before the final submission. Avoid installing unnecessary
libraries.

### `.env.example`

``` env
APP_ENV=development
API_HOST=127.0.0.1
API_PORT=8000
MAX_TM_STEPS=1000
CHROMA_PERSIST_DIRECTORY=./data/chroma
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Optional. Keep real secrets in .env, never commit them.
LLM_PROVIDER=
LLM_API_KEY=
```

### `.gitignore`

At minimum:

``` gitignore
.venv/
venv/
__pycache__/
*.py[cod]
.pytest_cache/
.env
data/chroma/
*.log
.DS_Store
.idea/
.vscode/
```

### `app/config.py`

Centralize environment settings. Do not hardcode API keys, local
absolute paths, or machine-specific directories in modules.

### `app/main.py`

Create the FastAPI app, register the router from
`api_integration/routes.py`, configure CORS for local frontend
development, and expose `/api/health`.

------------------------------------------------------------------------

## 9. Local setup and run commands

Requirements: - Python 3.10 or newer (agree on one version and test
it). - Git. - A modern browser. - Internet access for the first
embedding-model download, unless model weights are already available
locally.

Clone:

``` bash
git clone <YOUR_PUBLIC_GITHUB_REPOSITORY_URL>
cd natural-language-tm-simulator
```

Create and activate virtual environment:

**Windows PowerShell**

``` powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux/macOS**

``` bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

``` bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and adjust settings if required. Never
commit `.env`.

Ingest the RAG knowledge base (the integration owner must finalize the
exact CLI):

``` bash
python -m rag_pipeline.ingest
```

Start backend:

``` bash
uvicorn app.main:app --reload
```

Open API documentation:

``` text
http://127.0.0.1:8000/docs
```

Open `frontend/index.html` in a browser, or use a simple local static
server if required by browser fetch/CORS behavior. The frontend must
call the backend URL configured in `frontend/js/api.js`.

Run tests:

``` bash
pytest -q
```

**Note:** These commands are the target project workflow. Each owner
must ensure their module imports and runs from the repository root.
Member 6 finalizes any command that changes during integration and
updates this README.

------------------------------------------------------------------------

## 10. GitHub collaboration workflow

### One-time setup by repository owner

1.  Create a public GitHub repository.
2.  Add this README at the root.
3.  Add the six empty top-level contribution folders (a `.gitkeep` can
    preserve an empty folder).
4.  Add root setup files and shared schemas, or assign the integration
    owner to create them.
5.  Invite the five teammates as collaborators.
6.  Protect `main` if possible; require pull requests for merges.
7.  Create issues for each member using the deliverables in Section 5.

### Each member's workflow

1.  Clone the repository.
2.  Create a branch named `feature/<folder-name>`.
3.  Work only inside the assigned folder.
4.  Add the folder's own `README.md`.
5.  Add unit tests for the module in the agreed test location, or
    include module-local tests until the integration owner merges them
    into `tests/`.
6.  Run tests and verify imports from the repository root.
7.  Commit and push the branch.
8.  Open a pull request to `main`.
9.  Explain files added, public functions, dependencies, and test
    commands.
10. Resolve review comments.
11. Merge only after the integration owner confirms compatibility.

Example:

``` bash
git checkout -b feature/rule-parser
git add rule_parser/
git commit -m "Add TM rule parser and validator"
git push -u origin feature/rule-parser
```

Then open a pull request on GitHub.

### Critical collaboration rules

-   Do not upload files directly to `main` unless the repository owner
    explicitly permits it.
-   Do not modify another member's folder without coordination.
-   Do not rename public functions or JSON keys without telling the
    team.
-   Do not commit `.env`, API keys, virtual environments, ChromaDB local
    data, or large model weights.
-   Do not overwrite another member's work.
-   If a shared contract needs to change, open an issue or discuss it
    before changing code.
-   Every folder must have a README explaining installation (if any),
    files, public interfaces, and tests.
-   A folder is not complete merely because it uploads: it must pass its
    tests and integrate with the agreed interfaces.

------------------------------------------------------------------------

## 11. Instructions each member should give their ChatGPT

Every member should paste the following prompt into ChatGPT and attach
this root `README.md`. They should replace the role and folder
placeholders with their assigned details.

``` text
You are helping me implement ONE module of a six-person Python project:
"AI-Powered Natural Language Turing Machine Simulator".

Read the attached root README.md completely before writing code.

My assigned role: [ROLE]
My only contribution folder: [FOLDER PATH]

Your task:
1. Follow the README's architecture, folder ownership, shared schemas,
   public interfaces, naming conventions, and acceptance criteria exactly.
2. Generate every required file inside my assigned folder.
3. Do not generate or modify other members' folders.
4. Do not redesign the overall architecture or change shared JSON keys.
5. Use Python for backend modules. The frontend role uses HTML/CSS/JS.
6. Keep imports compatible with running commands from the repository root.
7. Add type hints, docstrings, clear error handling, and useful comments.
8. Add tests for my module and explain how to run them.
9. Do not use fake implementations, TODO-only functions, or hardcoded
   ACCEPT/REJECT outputs.
10. Do not invent dependencies. List any dependencies my folder requires
    so the integration owner can add them to requirements.txt.
11. Ensure my module communicates with other modules only through the
    public interfaces described in the root README.
12. If a required interface is unclear or conflicts with the README,
    identify the conflict before coding; do not silently invent a new API.

First, show the exact folder tree you will create.
Then provide the complete contents of every file in that folder.
Finally, provide:
- installation/setup instructions,
- public function signatures,
- example input and output,
- test commands,
- acceptance-criteria checklist,
- integration notes for the other five members.

I should be able to copy your generated folder into the repository
without manually rewriting its architecture.
```

### Role-specific placeholders

  Member   Role                                   Folder
  -------- -------------------------------------- --------------------
  1        Frontend and tape visualization        `frontend/`
  2        Turing Machine execution engine        `tm_engine/`
  3        Rule parser and validator              `rule_parser/`
  4        Natural-language interpreter           `nlp_interpreter/`
  5        RAG pipeline and knowledge base        `rag_pipeline/`
  6        API, machine builder and integration   `api_integration/`

------------------------------------------------------------------------

## 12. Testing plan

The project must test the full pipeline, not only individual functions.

### Unit tests

  Module            Test
  ----------------- ----------------------------------------------------
  Frontend          Form validation, API errors, trace rendering
  TM engine         Movement, writing, halting, step limit
  Rule parser       Syntax, comments, duplicates, line numbers
  Validator         States, alphabets, start and halting states
  NLP interpreter   Paraphrases, negation, parity, ambiguity
  RAG               Ingestion, retrieval, metadata, irrelevant queries
  API               Valid request, invalid request, end-to-end result

### End-to-end examples

For the language "binary strings ending in 1":

  Input    Expected
  -------- ----------
  `1`      ACCEPT
  `101`    ACCEPT
  `0001`   ACCEPT
  `0`      REJECT
  `100`    REJECT
  `""`     REJECT

For "binary strings with an even number of zeros":

  Input    Expected
  -------- ----------
  `11`     ACCEPT
  `00`     ACCEPT
  `1010`   ACCEPT
  `0`      REJECT
  `100`    REJECT
  `111`    ACCEPT

For "binary strings containing substring 101":

  Input     Expected
  --------- ----------
  `101`     ACCEPT
  `01010`   ACCEPT
  `111`     REJECT
  `1001`    REJECT
  `""`      REJECT

These are language-level expected results. The team must ensure each
generated machine actually produces them through simulation. Do not
hardcode these expected outputs into the engine.

Also test: - Empty input. - Invalid alphabet symbols. - Unsupported
condition. - Ambiguous condition. - Malformed transition. - Duplicate
transition. - Missing transition. - Maximum-step termination. - A
condition paraphrase not used in the original examples.

------------------------------------------------------------------------

## 13. Definition of done

The project is ready for demonstration when all of the following are
true:

-   [ ] All six contribution folders are merged into `main`.
-   [ ] Root setup instructions work from a clean clone.
-   [ ] Frontend communicates with the Python API.
-   [ ] Natural-language conditions are converted into normalized
    schemas.
-   [ ] Ambiguous/unsupported requests are handled honestly.
-   [ ] RAG knowledge ingestion and retrieval work.
-   [ ] Retrieved sources are visible to the user.
-   [ ] Machine builder produces complete, valid transition
    specifications for supported families.
-   [ ] Rule parser and validator reject invalid machines.
-   [ ] TM engine executes deterministically and returns a trace.
-   [ ] ACCEPT/REJECT is based only on actual machine execution.
-   [ ] Step limit is a separate result.
-   [ ] Unit and end-to-end tests pass.
-   [ ] No API keys or local secrets are committed.
-   [ ] Each member's folder contains its own README and documented
    interfaces.
-   [ ] A demo can be run from a fresh clone using the root README.

------------------------------------------------------------------------

## 14. Suggested final demonstration sequence

Use this order in the project presentation:

1.  Explain the problem: converting natural-language language conditions
    into formal TM simulations.
2.  Enter: "The binary string should end with 1."
3.  Show the interpreter's structured condition.
4.  Show the RAG retrieval panel and source documents.
5.  Show the generated machine's states and transition table.
6.  Show parser/validator success.
7.  Enter `101`.
8.  Run step-by-step and explain read, write, move, and state changes.
9.  Show ACCEPT.
10. Change input to `100` and show REJECT.
11. Try a paraphrased condition to demonstrate natural-language
    flexibility.
12. Try an unsupported or ambiguous condition to demonstrate safe
    handling.
13. Explain how the six modules connect and show the GitHub folder
    contributions.

### Questions the team should be ready to answer

-   What is a Turing Machine?
-   What is the transition function?
-   What is the difference between input alphabet and tape alphabet?
-   What are accept and reject states?
-   What happens when a transition is missing?
-   Why is the engine deterministic?
-   What is RAG, and why is it used here?
-   What is an embedding?
-   What is a vector database?
-   How does retrieval differ from generation?
-   How do you prevent an LLM from generating invalid transitions?
-   Why is the final ACCEPT/REJECT decision made by the TM engine?
-   What happens when a condition is unsupported?
-   What is the purpose of the maximum-step limit?

------------------------------------------------------------------------

## 15. Final instruction to the team

**Do not start by independently building six unrelated applications.**
This is one integrated project with six modules.

Before implementation, all six members must agree on: 1. Folder names
and ownership. 2. The normalized condition schema. 3. The machine
definition schema. 4. The transition representation. 5. The simulation
trace format. 6. The API request/response format.

Then each member builds only their assigned folder, tests it
independently, and submits a pull request. The integration owner
connects the modules and resolves compatibility issues.

The final product should demonstrate a complete, explainable pipeline:

**Natural Language → Interpretation → RAG Retrieval → TM Construction →
Rule Validation → TM Simulation → ACCEPT / REJECT.**
