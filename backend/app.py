import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, send_from_directory
from config import Config
from extensions import db, jwt, cors
from routes.auth import auth_bp
from routes.carbon import carbon_bp
from routes.insights import insights_bp


def create_app():
    app = Flask(__name__, static_folder='../frontend', static_url_path='')
    app.config.from_object(Config)

    # Init extensions
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r'/api/*': {'origins': '*'}})

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(carbon_bp)
    app.register_blueprint(insights_bp)

    # Serve frontend
    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/<path:path>')
    def catch_all(path):
        file_path = os.path.join(app.static_folder, path)
        if os.path.isfile(file_path):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, 'index.html')

    @app.errorhandler(404)
    def not_found(e):
        return send_from_directory(app.static_folder, 'index.html')

    # Create DB tables
    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5001)
