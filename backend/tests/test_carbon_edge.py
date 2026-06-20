import pytest
from models import CarbonEntry
from extensions import db
from datetime import date, timedelta

def test_calculate_no_data(client):
    resp = client.post('/api/carbon/calculate') # no json
    assert resp.status_code == 400

def test_calculate_invalid_data(client):
    resp = client.post('/api/carbon/calculate', json={'transport': 'invalid'})
    assert resp.status_code == 400

def test_submit_invalid_data(client, auth_headers):
    resp = client.post('/api/carbon/submit', json={'transport': 'invalid'}, headers=auth_headers)
    assert resp.status_code == 400

def test_submit_calculation_error(client, auth_headers):
    bad_data = {
        'transport': {'car_type': 'car_none', 'car_km_week': "string_instead_of_number"},
        'home_energy': {}, 'diet': {}, 'shopping': {}
    }
    resp = client.post('/api/carbon/submit', json=bad_data, headers=auth_headers)
    assert resp.status_code == 400

def test_calculate_calculation_error(client):
    bad_data = {
        'transport': {'car_type': 'car_none', 'car_km_week': "string_instead_of_number"},
        'home_energy': {}, 'diet': {}, 'shopping': {}
    }
    resp = client.post('/api/carbon/calculate', json=bad_data)
    assert resp.status_code == 400

def test_summary_two_entries(client, auth_headers, sample_inputs):
    client.post('/api/carbon/submit', json=sample_inputs, headers=auth_headers)
    
    # modify DB manually to make it a previous day
    with client.application.app_context():
        entries = CarbonEntry.query.all()
        entries[0].entry_date = date.today() - timedelta(days=30)
        db.session.commit()
        
    client.post('/api/carbon/submit', json=sample_inputs, headers=auth_headers)
    resp = client.get('/api/carbon/summary', headers=auth_headers)
    assert resp.status_code == 200
