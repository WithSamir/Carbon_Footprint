"""Tests for carbon calculation and submission routes."""

import pytest


class TestCalculate:
    """Test suite for the /api/carbon/calculate endpoint."""

    def test_calculate_success(self, client, sample_inputs):
        """Valid inputs return 200 with emission breakdown."""
        resp = client.post('/api/carbon/calculate', json=sample_inputs)
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'total_kg' in data
        assert 'transport_kg' in data
        assert 'diet_kg' in data
        assert 'home_energy_kg' in data
        assert 'shopping_kg' in data
        assert data['total_kg'] > 0

    def test_calculate_returns_benchmarks(self, client, sample_inputs):
        """Calculation includes benchmark comparison data."""
        resp = client.post('/api/carbon/calculate', json=sample_inputs)
        data = resp.get_json()
        assert 'benchmarks' in data
        assert 'global_avg_month' in data['benchmarks']
        assert 'national_avg_month' in data['benchmarks']
        assert 'paris_target_month' in data['benchmarks']

    def test_calculate_returns_annual_projection(self, client, sample_inputs):
        """Calculation includes annual projection."""
        resp = client.post('/api/carbon/calculate', json=sample_inputs)
        data = resp.get_json()
        assert 'annual_projection_kg' in data
        assert abs(data['annual_projection_kg'] - data['total_kg'] * 12) < 0.1

    def test_calculate_returns_percentile(self, client, sample_inputs):
        """Calculation includes percentile ranking."""
        resp = client.post('/api/carbon/calculate', json=sample_inputs)
        data = resp.get_json()
        assert 'percentile' in data
        assert 0 <= data['percentile'] <= 100

    def test_calculate_no_body(self, client):
        """Request with no JSON body returns 400."""
        resp = client.post('/api/carbon/calculate',
                           content_type='application/json')
        assert resp.status_code == 400

    def test_calculate_zero_emissions(self, client):
        """Minimal lifestyle returns low but non-negative emissions."""
        minimal = {
            'transport': {'car_type': 'car_none', 'car_km_week': 0,
                          'motorbike_km_week': 0, 'bus_km_week': 0,
                          'train_km_week': 0, 'flights_short_year': 0,
                          'flights_long_year': 0},
            'home_energy': {'home_size': 'studio',
                            'energy_source': 'electricity_kwh_renewable',
                            'heating_type': 'electricity_kwh_renewable',
                            'occupants': 1},
            'diet': {'diet_type': 'vegan_per_day',
                     'food_waste': 'none', 'local_food': 'always'},
            'shopping': {'new_clothes_month': 0,
                         'new_electronics_year': [],
                         'online_orders_week': 0},
            'country': 'GB',
        }
        resp = client.post('/api/carbon/calculate', json=minimal)
        data = resp.get_json()
        assert data['total_kg'] >= 0

    def test_calculate_different_countries(self, client, sample_inputs):
        """Different countries return different national benchmarks."""
        sample_inputs['country'] = 'US'
        resp_us = client.post('/api/carbon/calculate', json=sample_inputs)
        sample_inputs['country'] = 'IN'
        resp_in = client.post('/api/carbon/calculate', json=sample_inputs)
        us_avg = resp_us.get_json()['benchmarks']['national_avg_month']
        in_avg = resp_in.get_json()['benchmarks']['national_avg_month']
        assert us_avg != in_avg


class TestSubmit:
    """Test suite for the /api/carbon/submit endpoint."""

    def test_submit_success(self, client, auth_headers, sample_inputs):
        """Authenticated submission saves entry and returns XP."""
        resp = client.post('/api/carbon/submit',
                           json=sample_inputs, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.get_json()
        assert 'entry_id' in data
        assert 'xp_earned' in data
        assert data['xp_earned'] > 0

    def test_submit_requires_auth(self, client, sample_inputs):
        """Submission without JWT returns 401."""
        resp = client.post('/api/carbon/submit', json=sample_inputs)
        assert resp.status_code == 401


class TestHistory:
    """Test suite for the /api/carbon/history endpoint."""

    def test_history_returns_entries(self, client, auth_headers, sample_inputs):
        """History returns list of past entries."""
        # Submit an entry first
        client.post('/api/carbon/submit',
                     json=sample_inputs, headers=auth_headers)
        resp = client.get('/api/carbon/history', headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'entries' in data
        assert len(data['entries']) >= 1

    def test_history_requires_auth(self, client):
        """History without JWT returns 401."""
        resp = client.get('/api/carbon/history')
        assert resp.status_code == 401


class TestSummary:
    """Test suite for the /api/carbon/summary endpoint."""

    def test_summary_with_data(self, client, auth_headers, sample_inputs):
        """Summary returns dashboard data when entries exist."""
        client.post('/api/carbon/submit',
                     json=sample_inputs, headers=auth_headers)
        resp = client.get('/api/carbon/summary', headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['has_data'] is True
        assert 'latest' in data
        assert 'xp_level' in data

    def test_summary_no_data(self, client):
        """Summary returns has_data=False for new user with no entries."""
        import uuid
        email = f'empty_{uuid.uuid4().hex[:8]}@test.com'
        reg = client.post('/api/auth/register', json={
            'email': email, 'password': 'secure1234'})
        token = reg.get_json()['access_token']
        resp = client.get('/api/carbon/summary',
                          headers={'Authorization': f'Bearer {token}'})
        assert resp.status_code == 200
        assert resp.get_json()['has_data'] is False
