import pytest
from extensions import db
from models import UserAction, CarbonEntry

class TestInsights:
    def test_recommendations_no_auth(self, client):
        resp = client.get('/api/insights/recommendations')
        assert resp.status_code == 401

    def test_recommendations_success(self, client, auth_headers):
        resp = client.get('/api/insights/recommendations', headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'recommendations' in data
        assert len(data['recommendations']) > 0

    def test_recommendations_with_entry(self, client, auth_headers, sample_user, app):
        with app.app_context():
            entry = CarbonEntry(user_id=sample_user['id'], total_kg=100.0)
            db.session.add(entry)
            db.session.commit()
            
        resp = client.get('/api/insights/recommendations', headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'recommendations' in data

    def test_commit_action_success(self, client, auth_headers):
        resp = client.post('/api/insights/actions/commit', json={'action_id': 'switch-public-transit'}, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['action']['action_id'] == 'switch-public-transit'
        assert data['action']['status'] == 'pledged'

    def test_commit_action_no_body(self, client, auth_headers):
        resp = client.post('/api/insights/actions/commit', headers=auth_headers)
        assert resp.status_code == 400

    def test_commit_action_no_action_id(self, client, auth_headers):
        resp = client.post('/api/insights/actions/commit', json={}, headers=auth_headers)
        assert resp.status_code == 400

    def test_commit_action_not_found(self, client, auth_headers):
        resp = client.post('/api/insights/actions/commit', json={'action_id': 'non_existent_action'}, headers=auth_headers)
        assert resp.status_code == 404

    def test_commit_action_duplicate(self, client, auth_headers):
        client.post('/api/insights/actions/commit', json={'action_id': 'switch-public-transit'}, headers=auth_headers)
        resp = client.post('/api/insights/actions/commit', json={'action_id': 'switch-public-transit'}, headers=auth_headers)
        assert resp.status_code == 409

    def test_complete_action_success(self, client, auth_headers):
        client.post('/api/insights/actions/commit', json={'action_id': 'switch-public-transit'}, headers=auth_headers)
        resp = client.post('/api/insights/actions/complete', json={'action_id': 'switch-public-transit'}, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['action']['status'] == 'completed'

    def test_complete_action_no_body(self, client, auth_headers):
        resp = client.post('/api/insights/actions/complete', headers=auth_headers)
        assert resp.status_code == 400

    def test_complete_action_no_action_id(self, client, auth_headers):
        resp = client.post('/api/insights/actions/complete', json={}, headers=auth_headers)
        assert resp.status_code == 400

    def test_complete_action_not_pledged(self, client, auth_headers):
        resp = client.post('/api/insights/actions/complete', json={'action_id': 'switch-public-transit'}, headers=auth_headers)
        assert resp.status_code == 404

    def test_complete_action_already_completed(self, client, auth_headers):
        client.post('/api/insights/actions/commit', json={'action_id': 'switch-public-transit'}, headers=auth_headers)
        client.post('/api/insights/actions/complete', json={'action_id': 'switch-public-transit'}, headers=auth_headers)
        resp = client.post('/api/insights/actions/complete', json={'action_id': 'switch-public-transit'}, headers=auth_headers)
        assert resp.status_code == 409

    def test_my_actions_success(self, client, auth_headers):
        client.post('/api/insights/actions/commit', json={'action_id': 'switch-public-transit'}, headers=auth_headers)
        resp = client.get('/api/insights/actions/my', headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data['actions']) >= 1
        assert data['actions'][0]['action_id'] == 'switch-public-transit'
