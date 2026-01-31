"""Flask application factory."""
import os
from flask import Flask, jsonify
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

    # JWT error handlers for debugging
    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        print(f"JWT Invalid token: {error_string}")
        return jsonify({'error': f'Invalid token: {error_string}'}), 401

    @jwt.unauthorized_loader
    def unauthorized_callback(error_string):
        print(f"JWT Unauthorized: {error_string}")
        return jsonify({'error': f'Missing token: {error_string}'}), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        print(f"JWT Expired: {jwt_payload}")
        return jsonify({'error': 'Token has expired'}), 401

    @jwt.token_verification_failed_loader
    def token_verification_failed_callback(jwt_header, jwt_payload):
        print(f"JWT Verification failed: {jwt_payload}")
        return jsonify({'error': 'Token verification failed'}), 401

    # Configure CORS
    cors_origins = app.config.get('CORS_ORIGINS', '*')
    # Handle both comma-separated string and wildcard
    allowed_origins = cors_origins.split(',') if cors_origins != '*' else '*'

    CORS(app, resources={
        r"/api/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
            "expose_headers": ["Content-Type", "Authorization"]
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

    # Root endpoint for basic connectivity test
    @app.route('/')
    def root():
        """Root endpoint."""
        return {'message': 'Frames API', 'health': '/api/health', 'status': '/api/status'}, 200

    # Health check endpoint - MUST respond quickly for Railway
    @app.route('/api/health')
    def health_check():
        """Lightweight health check that responds immediately."""
        return {'status': 'healthy', 'message': 'Frames API is running'}, 200

    # Detailed status endpoint with database check
    @app.route('/api/status')
    def status_check():
        """Detailed status including database connection."""
        status = {
            'status': 'healthy',
            'message': 'Frames API is running',
            'environment': os.environ.get('FLASK_ENV', 'development')
        }

        # Check database connection (with timeout protection)
        try:
            # Set a statement timeout to prevent hanging
            db.session.execute(db.text('SET statement_timeout = 5000'))  # 5 second timeout
            db.session.execute(db.text('SELECT 1'))
            db.session.commit()
            status['database'] = 'connected'
        except Exception as e:
            status['database'] = 'disconnected'
            status['database_error'] = str(e)[:200]

        return status, 200

    # Debug endpoint to test JWT
    @app.route('/api/debug/token')
    def debug_token():
        from flask import request
        auth_header = request.headers.get('Authorization', 'Not provided')
        print(f"Auth header: {auth_header}")
        return {'auth_header': auth_header[:50] + '...' if len(auth_header) > 50 else auth_header}

    # Import models to register them with SQLAlchemy
    # Don't auto-create tables - use migrations in production
    try:
        from . import models
        print("✓ Models imported successfully")
    except Exception as e:
        print(f"⚠ Error importing models: {e}")

    # Only auto-create tables in development (not production)
    if os.environ.get('FLASK_ENV') == 'development':
        with app.app_context():
            try:
                db.create_all()
                print("✓ Database tables created (development mode)")
            except Exception as e:
                print(f"⚠ Database table creation failed: {e}")

    return app
