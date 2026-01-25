"""Flask application factory."""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from .config import Config

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Configure CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config.get('CORS_ORIGINS', '*').split(','),
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # Ensure upload folder exists
    upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(os.path.join(upload_folder, 'frames'), exist_ok=True)
    os.makedirs(os.path.join(upload_folder, 'walls'), exist_ok=True)
    os.makedirs(os.path.join(upload_folder, 'models'), exist_ok=True)

    # Register blueprints
    from .routes import auth, walls, pictures, models3d
    app.register_blueprint(auth.bp, url_prefix='/api/auth')
    app.register_blueprint(walls.bp, url_prefix='/api/walls')
    app.register_blueprint(pictures.bp, url_prefix='/api/pictures')
    app.register_blueprint(models3d.bp, url_prefix='/api/models')

    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy', 'message': 'Frames API is running'}

    return app
