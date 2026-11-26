"""API workflow tests with controlled teammate dependencies."""
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from app.main import app
from api_integration.routes import get_service_dependency
from api_integration.service import MachineService

CASES = [
    ('Starts with 1', 'starts_with', {'symbol': '1'}, '101', '011'),
    ('Ends with 1', 'ends_with', {'symbol': '1'}, '101', '110'),
    ('Contains 101', 'contains', {'substring': '101'}, '11010', '11100'),
    ('Does not contain 11', 'does_not_contain', {'substring': '11'}, '1010', '1101'),
    ('Even length', 'length_parity', {'parity': 'even'}, '1010', '101'),
    ('Even number of zeros', 'count_parity', {'symbol': '0', 'parity': 'even'}, '1001', '101'),
    ('Starts with 1 and ends with 0', 'starts_and_ends', {'start_symbol': '1', 'end_symbol': '0'}, '1010', '0010'),
    ('Exactly 101', 'exact_string', {'value': '101'}, '101', '1011'),
    ('Empty string', 'empty_or_nonempty', {'mode': 'empty'}, '', '1'),
    ('Non-empty string', 'empty_or_nonempty', {'mode': 'nonempty'}, '0', ''),
]


def interpret(condition):
    for text, family, parameters, _, _ in CASES:
        if text == condition:
            return {'family': family, 'parameters': deepcopy(parameters),
                    'alphabet': ['0', '1'], 'confidence': 1.0,
                    'needs_clarification': False}
    raise ValueError('Unknown test condition')


def retrieve(query, top_k=4):
    return [{'chunk_id': 'integration_test', 'source': 'synthetic-test',
             'text': 'Controlled reference data for testing.'}]


def parse(rules_text):
    transitions = {}
    for line in rules_text.splitlines():
        left, right = line.split('->')
        state, read = map(str.strip, left.split(','))
        next_state, write, direction = map(str.strip, right.split(','))
        transitions[(state, read)] = {'next_state': next_state,
                                      'write_symbol': write, 'direction': direction}
    return transitions


@pytest.fixture
def client():
    service = MachineService(interpreter=interpret, retriever=retrieve,
                             parser=parse, validator=lambda machine: machine)
    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_service_dependency] = lambda: service
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)


@pytest.mark.parametrize('condition,family,parameters,accepted,rejected', CASES,
                         ids=[case[0] for case in CASES])
def test_generate_all_families(client, condition, family, parameters, accepted, rejected):
    response = client.post('/api/machine/generate', json={'condition': condition})
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert data['condition']['family'] == family
    assert data['condition']['parameters'] == parameters
    assert data['machine']['transitions']
    assert data['rules_text']
    assert data['rag_sources'][0]['source'] == 'synthetic-test'


@pytest.mark.parametrize('condition,family,parameters,accepted,rejected', CASES,
                         ids=[case[0] for case in CASES])
@pytest.mark.parametrize('expected', ['ACCEPT', 'REJECT'])
def test_run_all_families(client, condition, family, parameters, accepted, rejected, expected):
    input_string = accepted if expected == 'ACCEPT' else rejected
    response = client.post('/api/machine/run', json={
        'condition': condition, 'input_string': input_string, 'max_steps': 1000})
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert data['status'] == expected
    assert data['reason'] == ('accept_state' if expected == 'ACCEPT' else 'reject_state')
    assert data['condition']['family'] == family
    assert data['trace']
    assert data['rules_text']
    assert data['rag_sources']
    assert data['final_state'] in data['machine']['accept_states' if expected == 'ACCEPT' else 'reject_states']
