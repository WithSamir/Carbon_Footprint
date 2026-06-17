"""
Flask extension instances for CarbonTrace.

Centralized initialization of Flask extensions to avoid circular imports.
Extensions are created here and initialized with the app in the factory.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS

db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()
