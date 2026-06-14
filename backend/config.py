import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'carbontrace-dev-secret-key-change-in-prod')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'carbontrace-jwt-secret-change-in-prod')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=30)
    
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'sqlite:///{os.path.join(BASE_DIR, "carbontrace.db")}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    EMISSION_FACTORS_PATH = os.path.join(DATA_DIR, 'emission_factors.json')
    ACTIONS_CATALOGUE_PATH = os.path.join(DATA_DIR, 'actions_catalogue.json')
