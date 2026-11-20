# Frontend & Tape Visualization Module

> **Module:** `frontend/`  
> **Role:** Frontend and Tape Visualization  
> **Tech Stack:** HTML5, CSS3, Modern Vanilla JavaScript (ES6+)  
> **Project:** AI-Powered Natural Language Turing Machine Simulator  

---

## 1. Overview & Purpose

The **Frontend and Tape Visualization** module provides the complete, production-grade graphical user interface for the AI-Powered Natural Language Turing Machine Simulator. It serves as the primary visual interface for automata students, professors, and researchers.

### Core Architectural Principle
> **The frontend never executes or fabricates Turing Machine transitions.**  
> The Python backend (`tm_engine`, `rule_parser`, `nlp_interpreter`, `rag_pipeline`, and `api_integration`) is the single source of truth. All transition rules, tape configurations, trace states, acceptance/rejection decisions, and RAG references are produced by the backend and visualized accurately in the browser.

---

## 2. Folder Structure

```
frontend/
├── index.html              # Semantic single-page application structure
├── css/
│   └── style.css           # Modern dark technical developer-tool interface styling
├── js/
│   ├── api.js              # Centralized backend HTTP communication & error handling
│   ├── tape.js             # Visual tape cell rendering & head tracking engine
│   ├── visualization.js    # State tuples, transition rules, trace history & RAG panels
│   └── app.js              # Application lifecycle, UI state, playback coordination
└── README.md               # Complete module documentation & integration guide
```

---

## 3. JavaScript File Responsibilities & Architecture

Each JavaScript file has a single, well-defined responsibility with zero circular logic:

| File | Namespace | Key Responsibilities |
| :--- | :--- | :--- |
| `js/api.js` | `window.TMApi` | - Manages backend URL configuration & persistence via `localStorage`<br>- Periodic health checks (`GET /api/health`)<br>- Machine compilation API calls (`POST /api/machine/generate`)<br>- Simulation execution API calls (`POST /api/machine/run`)<br>- Schema normalization for trace steps across backend variations<br>- Detailed HTTP and network error translation |
| `js/tape.js` | `window.TMTape` | - Generates tape cells dynamically with virtual bounds<br>- Supports **negative head positions** (e.g., when the TM head moves left past 0)<br>- Supports infinite tape expansion with padded blank cells (`B`)<br>- Visualizes the active read/write head with glowing indicator<br>- Smoothly auto-centers the active cell in the viewport<br>- Animates write updates on modified cells |
| `js/visualization.js` | `window.TMViz` | - Renders formal 7-tuple: $M = (Q, \Sigma, \Gamma, \delta, q_0, B, F)$<br>- Formats transition rules table: $\delta(q, a) \to (p, b, D)$<br>- Renders Step-by-Step Transition History table with clickable rows<br>- Fast-updates active row highlights during playback<br>- Renders deterministic simulation outcome (`ACCEPT`, `REJECT`, `STEP_LIMIT`, `NEEDS_CLARIFICATION`)<br>- Renders RAG knowledge base chunks with disclaimer badge |
| `js/app.js` | Internal | - Application bootstrap & DOM caching<br>- Preset example condition management<br>- Form input validation (handles empty string $\epsilon$, symbols, max steps)<br>- Playback engine: **Run**, **Step Forward**, **Step Backward**, **Pause**, **Reset**<br>- Step Scrubber progress bar binding<br>- Playback speed switching (0.5x, 1x, 2x, 5x)<br>- Settings modal interaction |

---

## 4. UI & Aesthetic Design

The interface follows a **modern developer-tool aesthetic** inspired by modern high-craft interfaces (Linear, VS Code, JetBrains):

- **Dark Technical Theme:** Deep slate/zinc canvas (`#080b11`, `#0d121d`) with high-contrast typography and subtle borders (`rgba(255, 255, 255, 0.08)`).
- **Luminous Visual Accents:** Cyan/sky accents for head pointer and reading symbols, emerald green for `ACCEPT` status, crimson rose for `REJECT`, and amber for warnings/limits.
- **Visual Infinite Tape:** Tape viewport features horizontal gradient masks on both edges to visually convey an unbounded tape that extends infinitely in both directions.
- **Responsive Layout:** CSS Grid and Flexbox with media query breakpoints for desktop (1540px max-width), laptop (1024px), tablet (768px), and mobile devices.

---

## 5. API Integration & Contracts

All requests originate from `frontend/js/api.js`.

### Default Endpoint
`http://127.0.0.1:8000` (Configurable at runtime via the "Configure URL" button in the header, persisted in `localStorage`).

### Supported Endpoints

#### 1. Health Check
- **Method:** `GET /api/health`
- **Response:**
  ```json
  { "status": "ok" }
  ```

#### 2. Machine Generation
- **Method:** `POST /api/machine/generate`
- **Request:**
  ```json
  {
    "condition": "The binary string should end with 1",
    "alphabet": ["0", "1"]
  }
  ```
- **Response:**
  ```json
  {
    "success": true,
    "condition": {
      "family": "ends_with",
      "parameters": { "symbol": "1" },
      "alphabet": ["0", "1"],
      "needs_clarification": false
    },
    "machine": {
      "start_state": "q0",
      "accept_states": ["q_accept"],
      "reject_states": ["q_reject"],
      "input_alphabet": ["0", "1"],
      "tape_alphabet": ["0", "1", "B"],
      "blank_symbol": "B",
      "transitions": [
        {
          "current_state": "q0",
          "read_symbol": "1",
          "next_state": "q_accept",
          "write_symbol": "1",
          "direction": "R"
        }
      ]
    },
    "rules_text": "q0, 1 -> q_accept, 1, R\n...",
    "rag_sources": [
      {
        "source": "ends_with_one.md",
        "topic": "ends_with",
        "content": "...",
        "score": 0.94
      }
    ]
  }
  ```

#### 3. Simulation Run
- **Method:** `POST /api/machine/run`
- **Request:**
  ```json
  {
    "condition": "The binary string should end with 1",
    "input_string": "101",
    "alphabet": ["0", "1"],
    "max_steps": 1000
  }
  ```
- **Response:**
  ```json
  {
    "success": true,
    "status": "ACCEPT",
    "reason": "accept_state",
    "steps": 4,
    "final_state": "q_accept",
    "final_tape": ["1", "0", "1", "B"],
    "head_position": 3,
    "trace": [
      {
        "step": 0,
        "current_state": "q0",
        "head_position": 0,
        "read_symbol": "1",
        "write_symbol": null,
        "direction": null,
        "next_state": null,
        "tape": ["1", "0", "1", "B"]
      },
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
    ],
    "rag_sources": [...],
    "explanation": "The validated machine reached its accept state."
  }
  ```

---

## 6. How Tape Visualization & Playback Work

### Virtual Coordinate System & Expansion
1. Turing machines can move left past index `0` into negative indices (`-1`, `-2`, etc.).
2. `tape.js` calculates the span:
   $$\text{min\_index} = \min(0, \text{head}) - 5$$
   $$\text{max\_index} = \max(\text{tape.length} - 1, \text{head}) + 5$$
3. It renders every cell within this span, filling empty slots outside the active tape with the blank symbol `B`.
4. Smooth auto-centering recalculates the container's `scrollLeft` whenever the head moves so the active cell remains centered in the viewport.

### Execution Controls Mechanics
- **Run / Play:** Starts a `setInterval` timer advancing one trace configuration per interval (default 500ms). When the final configuration is reached, playback halts and the final Result card is rendered.
- **Pause:** Halts the animation timer immediately without altering the current configuration or head position.
- **Step Forward:** Pauses auto-play and displays strictly configuration $k + 1$. Updates head pointer, tape cells, state badges, and table highlights.
- **Step Backward:** Pauses auto-play and rewinds to configuration $k - 1$.
- **Reset:** Rewinds directly to configuration $0$ (the initial machine configuration).
- **Scrubber Slider:** Direct random-access scrubbing to any step $0 \dots N - 1$ in the trace.
- **Clickable History Rows:** Clicking any row in the Transition History table jumps the tape instantly to that exact point in time.

---

## 7. How to Run the Frontend Locally

### Option A: Direct Browser Opening (No Server Required)
Because the codebase uses standard browser script loading without bundlers or cross-origin ES module imports, you can open `frontend/index.html` directly in any modern browser:
```bash
# Windows
start frontend/index.html

# macOS
open frontend/index.html

# Linux
xdg-open frontend/index.html
```

### Option B: Local Python HTTP Server
```bash
# From the repository root
python -m http.server 3000
# Then open http://localhost:3000/frontend/
```

### Option C: FastAPI Static Files Mounting
When Member 6 integrates the root application, `app/main.py` can serve the frontend:
```python
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
```

---

## 8. Verification & Test Scenarios

The frontend includes quick-preset buttons implementing the test cases specified in the project specification:

### Test Case 1: Binary strings ending in 1
- **Condition:** "The binary string should end with 1."
- **Alphabet:** `0, 1`
- **Expected Results:**
  - Input `1` $\to$ **ACCEPT**
  - Input `101` $\to$ **ACCEPT**
  - Input `0001` $\to$ **ACCEPT**
  - Input `0` $\to$ **REJECT**
  - Input `100` $\to$ **REJECT**
  - Input `""` (empty) $\to$ **REJECT**

### Test Case 2: Binary strings containing substring 101
- **Condition:** "Accept strings that contain the substring 101."
- **Alphabet:** `0, 1`
- **Expected Results:**
  - Input `101` $\to$ **ACCEPT**
  - Input `01010` $\to$ **ACCEPT**
  - Input `111` $\to$ **REJECT**
  - Input `1001` $\to$ **REJECT**
  - Input `""` $\to$ **REJECT**

### Edge Cases Handled by the Frontend
- **Empty input string $\epsilon$:** Passed as `""` to backend without throwing client validation error.
- **Backend Offline:** Status pill indicates "Offline", with actionable prompt to launch `uvicorn app.main:app --reload`.
- **Ambiguous Condition:** Displays backend clarification prompt in yellow notification card.
- **Step Limit Exceeded:** Displays amber status banner for `STEP_LIMIT`.

---

## 9. Integration Notes for Teammates

- **Member 2 (`tm_engine`):** Tape trace records are compatible with either naming convention (`head` or `head_position`, `state` or `current_state`, `read` or `read_symbol`).
- **Member 3 (`rule_parser`):** Rules table displays transition tuples accurately whether provided as structured lists or raw text.
- **Member 4 (`nlp_interpreter`):** If `needs_clarification: true` is returned, the frontend automatically displays `clarification_question` in an alert card.
- **Member 5 (`rag_pipeline`):** Retrieved source files, topics, match scores, and excerpts are displayed in the dedicated RAG Automata panel with an automata theory disclaimer.
- **Member 6 (`api_integration`):** CORS middleware is required on FastAPI (`allow_origins=["*"]`) for local browser fetch calls.
