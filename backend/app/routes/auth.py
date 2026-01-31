"""Authentication routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity
)
from app import db
from app.models import User

bp = Blueprint('auth', __name__)


@bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    if not all([email, username, password]):
        return jsonify({'error': 'Email, username, and password are required'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 409

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already taken'}), 409

    user = User(email=email, username=username)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        'message': 'User registered successfully',
        'user': user.to_dict(),
        'access_token': access_token
    }), 201


@bp.route('/login', methods=['POST'])
def login():
    """Login user and return JWT token."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({'error': 'Email and password are required'}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401

    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(),
        'access_token': access_token
    }), 200


@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current authenticated user."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({'user': user.to_dict()}), 200

@bp.route('/me', methods=['PUT'])
@jwt_required()
def update_current_user():
    """Update current user's profile."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()

    if 'username' in data:
        existing = User.query.filter_by(username=data['username']).first()
        if existing and existing.id != user.id:
            return jsonify({'error': 'Username already taken'}), 409
        user.username = data['username']

    if 'password' in data:
        user.set_password(data['password'])

    db.session.commit()

    return jsonify({
        'message': 'Profile updated',
        'user': user.to_dict()
    }), 200
