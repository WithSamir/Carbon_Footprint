"""Tests for authentication routes — registration, login, and user info."""

import pytest
import uuid


def _unique_email(prefix='test'):
    """Generate unique email to avoid DB conflicts across test runs."""
    return f'{prefix}_{uuid.uuid4().hex[:8]}@test.com'


class TestRegistration:
    """Test suite for the /api/auth/register endpoint."""

    def test_register_success(self, client):
        """Valid registration returns 201 with JWT token and user data."""
        email = _unique_email('new')
        resp = client.post('/api/auth/register', json={
            'email': email,
            'password': 'secure1234',
            'display_name': 'New User',
            'country': 'US',
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert 'access_token' in data
        assert data['user']['email'] == email
        assert data['user']['display_name'] == 'New User'

    def test_register_missing_email(self, client):
        """Registration without email returns 400."""
        resp = client.post('/api/auth/register', json={
            'password': 'secure1234',
        })
        assert resp.status_code == 400
        assert 'error' in resp.get_json()

    def test_register_missing_password(self, client):
        """Registration without password returns 400."""
        resp = client.post('/api/auth/register', json={
            'email': _unique_email('nopass'),
        })
        assert resp.status_code == 400

    def test_register_short_password(self, client):
        """Registration with password under 6 chars returns 400."""
        resp = client.post('/api/auth/register', json={
            'email': _unique_email('short'),
            'password': 'ab',
        })
        assert resp.status_code == 400
        assert 'Password' in resp.get_json()['error'] or 'password' in resp.get_json()['error'].lower()

    def test_register_duplicate_email(self, client, sample_user):
        """Registration with existing email returns 409."""
        resp = client.post('/api/auth/register', json={
            'email': sample_user['email'],
            'password': 'another1pass',
        })
        assert resp.status_code == 409

    def test_register_email_normalized(self, client):
        """Email is lowercased and trimmed during registration."""
        uid = uuid.uuid4().hex[:8]
        resp = client.post('/api/auth/register', json={
            'email': f'  UPPER{uid}@Test.COM  ',
            'password': 'secure1234',
        })
        assert resp.status_code == 201
        assert resp.get_json()['user']['email'] == f'upper{uid}@test.com'


class TestLogin:
    """Test suite for the /api/auth/login endpoint."""

    def test_login_success(self, client, sample_user):
        """Valid credentials return 200 with JWT token."""
        resp = client.post('/api/auth/login', json={
            'email': sample_user['email'],
            'password': sample_user['password'],
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'access_token' in data
        assert data['user']['email'] == sample_user['email']

    def test_login_wrong_password(self, client, sample_user):
        """Invalid password returns 401."""
        resp = client.post('/api/auth/login', json={
            'email': sample_user['email'],
            'password': 'wrongpassword',
        })
        assert resp.status_code == 401

    def test_login_nonexistent_email(self, client):
        """Non-existent email returns 401."""
        resp = client.post('/api/auth/login', json={
            'email': 'nobody@test.com',
            'password': 'anypass',
        })
        assert resp.status_code == 401

    def test_login_case_insensitive(self, client, sample_user):
        """Login works with uppercase email."""
        resp = client.post('/api/auth/login', json={
            'email': sample_user['email'].upper(),
            'password': sample_user['password'],
        })
        assert resp.status_code == 200


class TestMe:
    """Test suite for the /api/auth/me endpoint."""

    def test_me_authenticated(self, client, auth_headers):
        """Authenticated request returns current user info."""
        resp = client.get('/api/auth/me', headers=auth_headers)
        assert resp.status_code == 200
        assert 'user' in resp.get_json()

    def test_me_no_token(self, client):
        """Request without JWT returns 401."""
        resp = client.get('/api/auth/me')
        assert resp.status_code == 401

    def test_me_invalid_token(self, client):
        """Request with invalid JWT returns 422."""
        resp = client.get('/api/auth/me', headers={
            'Authorization': 'Bearer invalid-token'
        })
        assert resp.status_code in (401, 422)
