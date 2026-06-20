import pytest
from extensions import db
from models import User

def test_register_no_json(client):
    resp = client.post('/api/auth/register')
    assert resp.status_code == 400

def test_register_missing_fields(client):
    resp = client.post('/api/auth/register', json={'email': 'a@a.com'})
    assert resp.status_code == 400

def test_register_duplicate(client):
    client.post('/api/auth/register', json={'email': 'dup@test.com', 'password': 'pw'})
    resp = client.post('/api/auth/register', json={'email': 'dup@test.com', 'password': 'pw'})
    assert resp.status_code == 409

def test_login_no_json(client):
    resp = client.post('/api/auth/login')
    assert resp.status_code == 400

def test_login_missing_fields(client):
    resp = client.post('/api/auth/login', json={'email': 'a@a.com'})
    assert resp.status_code == 400
