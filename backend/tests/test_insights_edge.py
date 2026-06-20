import pytest

def test_commit_action_no_json(client, auth_headers):
    resp = client.post('/api/insights/actions/commit')
    assert resp.status_code == 400

def test_complete_action_no_json(client, auth_headers):
    resp = client.post('/api/insights/actions/complete')
    assert resp.status_code == 400
