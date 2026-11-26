# Project Setup and Execution Guide

## 1. Project Information

**Project:** AI and RAG-Based Turing Machine Simulation

**Component:** API Integration

**Developer:** Saakshi Sharma

## 2. Prerequisites

Install the following software:

- Python 3.12 (tested with Python 3.12.10)
- Git
- Visual Studio Code
- Web browser
- Internet connection for dependency installation

## 3. Obtain the Project

Clone the team's repository:

```powershell
git clone https://github.com/Mayank-669-79/AI-and-RAG-based-Turing-Machine-Simulation.git
```

Navigate to the project directory:

```powershell
cd AI-and-RAG-based-Turing-Machine-Simulation
```

Alternatively, download and extract the project ZIP containing the latest integration implementation.

Ensure the integration developer's changes are included before proceeding.

## 4. Create a Virtual Environment

Verify the installed Python version:

```powershell
py -3.12 --version
```

Create a virtual environment:

```powershell
py -3.12 -m venv .venv
```

Activate the virtual environment on Windows PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

For Linux or macOS:

```bash
source .venv/bin/activate
```

Verify the active Python version:

```powershell
python --version
```

## 5. Install Dependencies

Upgrade pip:

```powershell
python -m pip install --upgrade pip
```

Install project dependencies:

```powershell
python -m pip install -r requirements.txt
```

Verify dependency compatibility:

```powershell
python -m pip check
```

Expected output:

```text
No broken requirements found.
```

Additional teammate-specific dependencies and configuration may be required for the actual NLP and RAG implementations.

## 6. Expected Project Structure

```text
AI-and-RAG-based-Turing-Machine-Simulation/
    api_integration/
    app/
    frontend/
    nlp_interpreter/
    rag_pipeline/
    rule_parser/
    tm_engine/
    tests/
    requirements.txt
    pyproject.toml
    demo_app.py
```

The NLP interpreter and rule parser directories must be supplied by the respective teammates if they are missing.

The demo application is intended for temporary development and testing.

## 7. Verify Integration Dependencies

Run the following commands individually:

```powershell
python -c "from nlp_interpreter import interpret_condition"
```

```powershell
python -c "from rag_pipeline import retrieve_context"
```

```powershell
python -c "from rule_parser import parse_rules, validate_machine"
```

```powershell
python -c "from tm_engine import run_machine"
```

```powershell
python -c "from api_integration.service import MachineService"
```

All required imports must succeed before complete production integration.

## 8. Run the Production Backend

From the project root, execute:

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

Backend URL:

http://127.0.0.1:8000

Swagger API documentation:

http://127.0.0.1:8000/docs

Health check:

http://127.0.0.1:8000/api/health

Expected health response:

```json
{
  "status": "ok"
}
```

A successful health response confirms that the server is running, not that every integration dependency is available.

## 9. Run the Frontend

Open a second terminal from the project root.

Execute:

```powershell
python -m http.server 5500 --directory frontend
```

Open the following URL in a browser:

http://localhost:5500

Keep both backend and frontend terminals running during execution.

## 10. Run the Temporary Demo

If actual teammate dependencies are unavailable, use the temporary demo application, provided it is included in the project.

```powershell
python -m uvicorn demo_app:app --reload --port 8000
```

The demo uses mock NLP, RAG, parser and validator dependencies.

The mock interpreter generates a machine for strings ending with 1, regardless of the supplied natural-language condition.

The demo is not a substitute for complete production integration.

Do not run the demo and production backend simultaneously on port 8000.

## 11. Example Execution

Enter the following condition:

```text
Accept strings ending with 1
```

Enter the input string:

```text
101
```

Generate and execute the machine.

Expected result:

```text
ACCEPT
```

Additional example inputs:

| Input | Expected Result |
|---|---|
| 101 | ACCEPT |
| 110 | REJECT |
| 111 | ACCEPT |
| 000 | REJECT |
| 1021 | Invalid input symbol |
| Empty string | REJECT |

These examples are suitable for the current demo implementation.

## 12. Run Automated Tests

Execute the complete test suite:

```powershell
python -m pytest -q
```

Latest confirmed local result:

```text
236 passed in 6.81s
```

Run individual integration test suites:

```powershell
python -m pytest tests/test_machine_builder.py -v
python -m pytest tests/test_response_formatter.py -v
python -m pytest tests/test_service.py -v
python -m pytest tests/test_api.py -v
python -m pytest tests/test_integration_workflow.py -v
python -m pytest tests/test_execution_trace.py -v
```

The total test count may change after additional teammate tests are integrated.

## 13. Troubleshooting

| Problem | Possible Solution |
|---|---|
| Python not recognized | Verify Python installation |
| ModuleNotFoundError | Install dependencies or obtain missing teammate modules |
| Port already in use | Stop the existing server |
| HTTP 503 | Verify integration dependencies |
| HTTP 422 | Check request parameters |
| Frontend connection error | Verify backend availability and API URL |
| CORS error | Verify permitted frontend origin |
| Tests not detected | Verify test files exist and are saved |
| RAG retrieval failure | Check knowledge base, dependencies and retrieval configuration |

## 14. Security and Configuration

- Do not commit the virtual environment.
- Do not commit API keys or credentials.
- Do not commit Python cache files.
- Configure external services according to teammate documentation.
- Keep production and mock-based testing configurations separate.

## 15. Stop the Application

Press Ctrl + C in both server terminals.

Deactivate the virtual environment:

```powershell
deactivate
```

## 16. Current Implementation Status

The core integration implementation has passed all 236 automated tests on the developer's local machine.

Final integration with actual teammate modules and complete production end-to-end testing remain pending.