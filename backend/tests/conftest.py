"""Shared pytest fixtures for CarbonTrace test suite."""

import os
import sys
import pytest
import tempfile

# Ensure backend is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app
from extensions import db as _db
from models import User, CarbonEntry, UserAction
import bcrypt


@pytest.fixture(scope='session')
def app():
    """Create a Flask application configured for testing."""
    test_db_fd, test_db_path = tempfile.mkstemp(suffix='.db')
    os.environ['DATABASE_URL'] = f'sqlite:///{test_db_path}'
    os.environ['SECRET_KEY'] = 'test-secret-key'
    os.environ['JWT_SECRET_KEY'] = 'test-jwt-secret'

    application = create_app()
    application.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{test_db_path}',
    })

    with application.app_context():
        _db.create_all()

    yield application

    # Cleanup
    os.close(test_db_fd)
    os.unlink(test_db_path)


@pytest.fixture(scope='function')
def client(app):
    """Provide a Flask test client with application context."""
    with app.app_context():
        with app.test_client() as c:
            yield c


@pytest.fixture
def sample_user(app):
    """Create and return a sample user for testing."""
    with app.app_context():
        # Cleanup any existing user with this email
        existing = User.query.filter_by(email='testuser@example.com').first()
        if existing:
            UserAction.query.filter_by(user_id=existing.id).delete()
            CarbonEntry.query.filter_by(user_id=existing.id).delete()
            _db.session.delete(existing)
            _db.session.commit()

        hashed = bcrypt.hashpw(
            'testpass1'.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        user = User(
            email='testuser@example.com',
            password_hash=hashed,
            display_name='Test User',
            country='GB',
        )
        _db.session.add(user)
        _db.session.commit()
        user_id = user.id
        yield {'id': user_id, 'email': 'testuser@example.com', 'password': 'testpass1'}
        # Cleanup
        UserAction.query.filter_by(user_id=user_id).delete()
        CarbonEntry.query.filter_by(user_id=user_id).delete()
        User.query.filter_by(id=user_id).delete()
        _db.session.commit()


@pytest.fixture
def auth_headers(client, sample_user):
    """Return JWT auth headers for the sample user."""
    resp = client.post('/api/auth/login', json={
        'email': sample_user['email'],
        'password': sample_user['password'],
    })
    token = resp.get_json()['access_token']
    return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}


@pytest.fixture
def sample_inputs():
    """Return standard calculator input data for testing."""
    return {
        'transport': {
            'car_type': 'car_petrol_per_km',
            'car_km_week': 100,
            'motorbike_km_week': 0,
            'bus_km_week': 20,
            'train_km_week': 20,
            'flights_short_year': 2,
            'flights_long_year': 1,
        },
        'home_energy': {
            'home_size': 'medium',
            'energy_source': 'electricity_kwh_grid',
            'heating_type': 'natural_gas_kwh',
            'occupants': 2,
        },
        'diet': {
            'diet_type': 'meat_medium_per_day',
            'food_waste': 'medium',
            'local_food': 'sometimes',
        },
        'shopping': {
            'new_clothes_month': 2,
            'new_electronics_year': ['laptop'],
            'online_orders_week': 3,
        },
        'country': 'GB',
    }
