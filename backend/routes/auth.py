"""
Authentication routes for CarbonTrace.

Provides user registration, login, and profile retrieval
with JWT token-based authentication and input validation.
"""

import re
import logging
from flask import Blueprint, request, jsonify
import bcrypt
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from extensions import db
from models import User

logger = logging.getLogger('carbontrace.auth')

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Email validation regex (RFC 5322 simplified)
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# Security constraints
MIN_PASSWORD_LENGTH = 8
MAX_EMAIL_LENGTH = 255
MAX_DISPLAY_NAME_LENGTH = 100


def _validate_email(email: str) -> str | None:
    """Validate and normalize email address. Returns error message or None."""
    if not email:
        return 'Email is required'
    if len(email) > MAX_EMAIL_LENGTH:
        return f'Email must be under {MAX_EMAIL_LENGTH} characters'
    if not EMAIL_REGEX.match(email):
        return 'Please provide a valid email address'
    return None


def _validate_password(password: str) -> str | None:
    """Validate password strength. Returns error message or None."""
    if not password:
        return 'Password is required'
    if len(password) < MIN_PASSWORD_LENGTH:
        return f'Password must be at least {MIN_PASSWORD_LENGTH} characters'
    if not any(c.isdigit() for c in password):
        return 'Password must contain at least one number'
    if not any(c.isalpha() for c in password):
        return 'Password must contain at least one letter'
    return None


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user account.

    Expects JSON: {email, password, display_name?, country?}
    Returns: JWT access_token + user profile (201)
    Errors: 400 (validation), 409 (duplicate email)
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    display_name = data.get('display_name', '').strip()[:MAX_DISPLAY_NAME_LENGTH]
    country = data.get('country', 'GBR').strip()[:3]

    # Input validation
    email_err = _validate_email(email)
    if email_err:
        return jsonify({'error': email_err}), 400

    password_err = _validate_password(password)
    if password_err:
        return jsonify({'error': password_err}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'An account with this email already exists'}), 409

    # Hash password with bcrypt (salted)
    hashed = bcrypt.hashpw(
        password.encode('utf-8'), bcrypt.gensalt()
    ).decode('utf-8')

    user = User(
        email=email,
        password_hash=hashed,
        display_name=display_name or None,
        country=country,
    )
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=user.id)
    logger.info('New user registered: %s', email)
    return jsonify({'access_token': token, 'user': user.to_dict()}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate an existing user.

    Expects JSON: {email, password}
    Returns: JWT access_token + user profile (200)
    Errors: 401 (invalid credentials)
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    # Use constant-time comparison to prevent timing attacks
    user = User.query.filter_by(email=email).first()
    if not user:
        # Still hash a dummy password to prevent timing-based user enumeration
        bcrypt.hashpw(b'dummy', bcrypt.gensalt())
        return jsonify({'error': 'Invalid email or password'}), 401

    if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({'error': 'Invalid email or password'}), 401

    token = create_access_token(identity=user.id)
    logger.info('User logged in: %s', email)
    return jsonify({'access_token': token, 'user': user.to_dict()}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    """
    Retrieve the current authenticated user's profile.

    Requires: Valid JWT Bearer token
    Returns: User profile data (200)
    """
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': user.to_dict()}), 200
