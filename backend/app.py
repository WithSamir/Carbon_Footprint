"""
CarbonTrace — Flask Application Factory.

Creates and configures the Flask application with security headers,
CORS, JWT authentication, database ORM, response compression,
structured logging, and frontend static file serving.
"""

import os
import sys
import logging

# Add backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, send_from_directory, request, jsonify
from config import Config
from extensions import db, jwt, cors
from routes.auth import auth_bp
from routes.carbon import carbon_bp
from routes.insights import insights_bp

# ── Structured Logging ─────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger('carbontrace')


def create_app() -> Flask:
    """
    Application factory for CarbonTrace.

    Returns:
        Flask: Configured Flask application instance.
    """
    app = Flask(__name__, static_folder='../frontend', static_url_path='')
    app.config.from_object(Config)

    # ── Init Extensions ────────────────────────────────────────────────────
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r'/api/*': {'origins': '*'}})

    # ── Register Blueprints ────────────────────────────────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(carbon_bp)
    app.register_blueprint(insights_bp)

    # ── Security Headers Middleware ────────────────────────────────────────
    @app.after_request
    def set_security_headers(response):
        """Add security headers to every response (OWASP best practices)."""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = (
            'camera=(), microphone=(), geolocation=(self)'
        )
        response.headers['Strict-Transport-Security'] = (
            'max-age=31536000; includeSubDomains'
        )
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'"
        )
        return response

    # ── Request Logging ────────────────────────────────────────────────────
    @app.before_request
    def log_request():
        """Log incoming API requests for monitoring."""
        if request.path.startswith('/api/'):
            logger.info(
                'Request: %s %s from %s',
                request.method, request.path, request.remote_addr
            )

    # ── Global Error Handlers ──────────────────────────────────────────────
    @app.errorhandler(400)
    def bad_request(e):
        """Handle malformed requests."""
        return jsonify({'error': 'Bad request', 'message': str(e)}), 400

    @app.errorhandler(405)
    def method_not_allowed(e):
        """Handle unsupported HTTP methods."""
        return jsonify({'error': 'Method not allowed'}), 405

    @app.errorhandler(429)
    def rate_limited(e):
        """Handle rate-limited requests."""
        return jsonify({'error': 'Too many requests. Please slow down.'}), 429

    @app.errorhandler(500)
    def internal_error(e):
        """Handle unexpected server errors without leaking details."""
        logger.error('Internal server error: %s', str(e))
        return jsonify({'error': 'Internal server error'}), 500

    # ── Serve Frontend ─────────────────────────────────────────────────────
    @app.route('/')
    def index():
        """Serve the landing page."""
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/<path:path>')
    def catch_all(path: str):
        """Serve static files or fall back to index.html for SPA routing."""
        file_path = os.path.join(app.static_folder, path)
        if os.path.isfile(file_path):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, 'index.html')

    @app.errorhandler(404)
    def not_found(e):
        """Serve index.html for unmatched routes (SPA fallback)."""
        return send_from_directory(app.static_folder, 'index.html')

    # ── Create DB Tables Safely ────────────────────────────────────────────
    with app.app_context():
        db.metadata.create_all(db.engine, checkfirst=True)
        logger.info('Database tables verified.')

    logger.info('CarbonTrace application initialized successfully.')
    return app


# Create app instance for Gunicorn (production)
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
