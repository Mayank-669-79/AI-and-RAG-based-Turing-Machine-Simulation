"""Verify API execution traces against generated transition rules."""
import pytest
from tests.test_integration_workflow import client, CASES


def check_trace(data, input_string):
    trace = data['trace']
    machine = data['machine']
    blank = machine['blank_symbol']
    rules = {(r['current_state'], r['read_symbol']): r for r in machine['transitions']}
    assert len(trace) == data['steps'] + 1
    assert [r['step'] for r in trace] == list(range(len(trace)))
    assert trace[0]['state'] == machine['start_state']
    assert trace[0]['head'] == 0
    assert trace[0]['tape'] == (list(input_string) or [blank])
    assert trace[0]['write'] is None and trace[0]['move'] is None
    for previous, current in zip(trace, trace[1:]):
        tape = previous['tape'].copy()
        head = previous['head']
        rule = rules[(previous['state'], tape[head])]
        tape[head] = rule['write_symbol']
        move = rule['direction']
        head += {'L': -1, 'R': 1, 'S': 0}[move]
        if head < 0:
            tape.insert(0, blank)
            head = 0
        elif head == len(tape):
            tape.append(blank)
        assert current['state'] == rule['next_state']
        assert current['write'] == rule['write_symbol']
        assert current['move'] == move
        assert current['head'] == head
        assert current['tape'] == tape
        assert current['read'] == tape[head]
    assert trace[-1]['state'] == data['final_state']
    assert trace[-1]['head'] == data['head_position']
    assert trace[-1]['tape'] == data['final_tape']


@pytest.mark.parametrize('case', CASES, ids=[c[0] for c in CASES])
@pytest.mark.parametrize('accepted', [True, False])
def test_trace_all_families(client, case, accepted):
    input_string = case[3 if accepted else 4]
    response = client.post('/api/machine/run', json={'condition': case[0], 'input_string': input_string})
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == ('ACCEPT' if accepted else 'REJECT')
    check_trace(data, input_string)


def test_step_limit_trace(client):
    response = client.post('/api/machine/run', json={'condition': 'Ends with 1', 'input_string': '10101', 'max_steps': 2})
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'STEP_LIMIT'
    assert data['steps'] == 2
    check_trace(data, '10101')
