"""Automated tests for the FastAPI integration endpoints."""

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from api_integration.routes import get_service_dependency
from api_integration.service import MachineService

GENERATE_URL = "/api/machine/generate"
RUN_URL = "/api/machine/run"

def mock_interpreter(condition):
    return {
        "family": "ends_with",
        "parameters": {"symbol": "1"},
        "alphabet": ["0", "1"],
        "confidence": 1.0,
        "needs_clarification": False,
    }

def mock_retriever(query, top_k=4):
    return [
        {
            "chunk_id": "test_001",
            "source": "automata.md",
            "topic": "ends_with",
            "text": "Track the last symbol.",
            "distance": 0.12,
        }
    ]

def mock_parser(rules_text):
    transitions = {}

    for line in rules_text.splitlines():
        left, right = line.split("->")

        current_state, read_symbol = [
            item.strip() for item in left.split(",")
        ]

        next_state, write_symbol, direction = [
            item.strip() for item in right.split(",")
        ]

        transitions[(current_state, read_symbol)] = {
            "next_state": next_state,
            "write_symbol": write_symbol,
            "direction": direction,
        }

    return transitions

def mock_validator(machine):
    return machine

@pytest.fixture
def service():
    return MachineService(
        interpreter=Mock(side_effect=mock_interpreter),
        retriever=Mock(side_effect=mock_retriever),
        parser=Mock(side_effect=mock_parser),
        validator=Mock(side_effect=mock_validator),
    )

@pytest.fixture
def client(service):
    previous_overrides = app.dependency_overrides.copy()

    app.dependency_overrides[get_service_dependency] = (
        lambda: service
    )

    try:
        with TestClient(app) as test_client:
            yield test_client

    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)

def test_health_endpoint(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_generate_endpoint(client):
    response = client.post(
        GENERATE_URL,
        json={
            "condition": "Accept strings ending with 1",
            "alphabet": ["0", "1"],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["machine"]["transitions"]
    assert data["rules_text"]
    assert data["rag_sources"]

@pytest.mark.parametrize(
    "input_string, expected_status",
    [
        ("101", "ACCEPT"),
        ("110", "REJECT"),
        ("111", "ACCEPT"),
        ("000", "REJECT"),
        ("", "REJECT"),
    ],
)
def test_run_endpoint(
    client,
    input_string,
    expected_status,
):
    response = client.post(
        RUN_URL,
        json={
            "condition": "Accept strings ending with 1",
            "alphabet": ["0", "1"],
            "input_string": input_string,
            "max_steps": 1000,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["status"] == expected_status
    assert data["trace"]
    assert "steps" in data
    assert "final_state" in data
    assert "final_tape" in data
    assert "head_position" in data

def test_step_limit(client):
    response = client.post(
        RUN_URL,
        json={
            "condition": "Accept strings ending with 1",
            "input_string": "101010",
            "max_steps": 2,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "STEP_LIMIT"
    assert data["reason"] == "max_steps"

def test_invalid_input_symbol(client):
    response = client.post(
        RUN_URL,
        json={
            "condition": "Accept strings ending with 1",
            "input_string": "1021",
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_INPUT_SYMBOL"

def test_missing_condition(client):
    response = client.post(
        GENERATE_URL,
        json={"alphabet": ["0", "1"]},
    )

    assert response.status_code == 422

def test_empty_condition(client):
    response = client.post(
        GENERATE_URL,
        json={"condition": ""},
    )

    assert response.status_code == 422

def test_whitespace_condition(client):
    response = client.post(
        GENERATE_URL,
        json={"condition": "   "},
    )

    assert response.status_code == 400

    assert response.json()["error"]["code"] == (
        "INVALID_CONDITION"
    )

@pytest.mark.parametrize("max_steps", [0, -1, 100001])
def test_invalid_step_limit(client, max_steps):
    response = client.post(
        RUN_URL,
        json={
            "condition": "Accept strings ending with 1",
            "input_string": "101",
            "max_steps": max_steps,
        },
    )

    assert response.status_code == 422

def test_unexpected_request_field(client):
    response = client.post(
        GENERATE_URL,
        json={
            "condition": "Accept strings ending with 1",
            "unexpected_field": "invalid",
        },
    )

    assert response.status_code == 422

def test_alphabet_mismatch(client):
    response = client.post(
        GENERATE_URL,
        json={
            "condition": "Accept strings ending with 1",
            "alphabet": ["a", "b"],
        },
    )

    assert response.status_code == 400

    assert response.json()["error"]["code"] == (
        "ALPHABET_MISMATCH"
    )

def test_ambiguous_condition(client, service):
    service.interpreter.side_effect = None

    service.interpreter.return_value = {
        "needs_clarification": True,
        "clarification_question": "Which symbol?",
    }

    response = client.post(
        GENERATE_URL,
        json={"condition": "Accept some strings"},
    )

    assert response.status_code == 422

    data = response.json()

    assert data["success"] is False
    assert data["error"]["code"] == "AMBIGUOUS_CONDITION"
    assert data["clarification_question"] == "Which symbol?"

def test_interpreter_failure(client, service):
    service.interpreter.side_effect = RuntimeError(
        "Interpreter unavailable"
    )

    response = client.post(
        GENERATE_URL,
        json={"condition": "Test condition"},
    )

    assert response.status_code == 500

    assert response.json()["error"]["code"] == (
        "INTERPRETATION_ERROR"
    )

def test_retrieval_failure(client, service):
    service.retriever.side_effect = RuntimeError(
        "Retriever unavailable"
    )

    response = client.post(
        GENERATE_URL,
        json={"condition": "Test condition"},
    )

    assert response.status_code == 503

    assert response.json()["error"]["code"] == (
        "RETRIEVAL_ERROR"
    )

def test_parser_failure(client, service):
    service.parser.side_effect = ValueError(
        "Invalid rules"
    )

    response = client.post(
        GENERATE_URL,
        json={"condition": "Test condition"},
    )

    assert response.status_code == 500

    assert response.json()["error"]["code"] == (
        "MACHINE_VALIDATION_ERROR"
    )

@pytest.mark.parametrize(
    "endpoint",
    [GENERATE_URL, RUN_URL],
)
def test_service_unavailable(client, endpoint):
    app.dependency_overrides[get_service_dependency] = (
        lambda: None
    )

    response = client.post(
        endpoint,
        json={"condition": "Test condition"},
    )

    assert response.status_code == 503

    assert response.json()["error"]["code"] == (
        "SERVICE_UNAVAILABLE"
    )

def test_unknown_endpoint(client):
    response = client.get("/api/unknown")

    assert response.status_code == 404

def test_invalid_http_method(client):
    response = client.get(GENERATE_URL)

    assert response.status_code == 405

def test_openapi_schema(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/api/health" in paths
    assert GENERATE_URL in paths
    assert RUN_URL in paths

def test_reordered_alphabet(client):
    response = client.post(
        GENERATE_URL,
        json={
            "condition": "Accept strings ending with 1",
            "alphabet": ["1", "0"],
        },
    )
    assert response.status_code == 200
    assert response.json()["success"] is True


@pytest.mark.parametrize(
    "alphabet", [[], ["0", "0"], ["0", "B"], ["01", "1"], ["", "1"]]
)
def test_invalid_alphabet_request(client, alphabet):
    response = client.post(
        GENERATE_URL,
        json={
            "condition": "Accept strings ending with 1",
            "alphabet": alphabet,
        },
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_ALPHABET"


@pytest.mark.parametrize("payload", [{}, {"condition": ""}, {"condition": "test", "extra": True}])
def test_standard_validation_error(client, payload):
    response = client.post(GENERATE_URL, json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_REQUEST"
    assert data["error"]["details"]["errors"]


@pytest.mark.parametrize("path, code, status", [('/api/unknown', 'NOT_FOUND', 404), (GENERATE_URL, 'METHOD_NOT_ALLOWED', 405)])
def test_standard_http_error(client, path, code, status):
    response = client.get(path)
    assert response.status_code == status
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == code
    if status == 405:
        assert 'POST' in response.headers['allow']


def test_malformed_json_error(client):
    response = client.post(GENERATE_URL, content='{', headers={'Content-Type': 'application/json'})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


@pytest.mark.parametrize("url", [GENERATE_URL, RUN_URL])
def test_real_dependency_failure_is_safe(monkeypatch, caplog, url):
    from api_integration import routes

    loader = Mock(side_effect=ImportError("private dependency detail"))
    monkeypatch.setattr(routes, "get_service", loader)
    with TestClient(app) as test_client:
        response = test_client.post(url, json={"condition": "Accept strings ending with 1"})
        assert test_client.get("/api/health").status_code == 200
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert "private dependency detail" not in response.text
    assert "Integration dependency initialization failed" in caplog.text


def test_dependency_retry(monkeypatch, service):
    from api_integration import routes

    loader = Mock(side_effect=[ImportError("not ready"), service])
    monkeypatch.setattr(routes, "get_service", loader)
    with TestClient(app) as test_client:
        payload = {"condition": "Accept strings ending with 1"}
        assert test_client.post(GENERATE_URL, json=payload).status_code == 503
        assert test_client.post(GENERATE_URL, json=payload).status_code == 200
    assert loader.call_count == 2


def test_dependency_loader_retries_and_caches(monkeypatch):
    import sys
    from types import ModuleType
    from api_integration import routes

    nlp = ModuleType("nlp_interpreter")
    rag = ModuleType("rag_pipeline")
    parser = ModuleType("rule_parser")
    nlp.interpret_condition = None
    rag.retrieve_context = mock_retriever
    parser.parse_rules = mock_parser
    parser.validate_machine = mock_validator
    for module in (nlp, rag, parser):
        monkeypatch.setitem(sys.modules, module.__name__, module)
    routes.get_service.cache_clear()
    try:
        with pytest.raises(TypeError, match="interpret_condition"):
            routes.get_service()
        nlp.interpret_condition = mock_interpreter
        first = routes.get_service()
        assert isinstance(first, MachineService)
        assert routes.get_service() is first
    finally:
        routes.get_service.cache_clear()
