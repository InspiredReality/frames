"""Wall routes for managing virtual walls."""
import os
from PIL import Image as PILImage
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from sqlalchemy.orm.attributes import flag_modified
from app import db
from app.models import Wall
from app.services.image_processor import process_wall_image

bp = Blueprint('walls', __name__)


def allowed_file(filename):
    """Check if file extension is allowed."""
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


@bp.route('', methods=['GET'])
@jwt_required()
def get_walls():
    """Get all walls for the current user."""
    user_id = int(get_jwt_identity())
    walls = db.session.query(Wall).filter_by(user_id=user_id).order_by(Wall.created_at.desc()).all()

    return jsonify({
        'walls': [w.to_dict(include_placements=True) for w in walls]
    }), 200


@bp.route('/<int:wall_id>', methods=['GET'])
@jwt_required()
def get_wall(wall_id):
    """Get a specific wall by ID with its assigned frames."""
    user_id = int(get_jwt_identity())
    wall = db.session.query(Wall).filter_by(id=wall_id, user_id=user_id).first()

    if not wall:
        return jsonify({'error': 'Wall not found'}), 404

    return jsonify({'wall': wall.to_dict(include_frames=True)}), 200


@bp.route('', methods=['POST'])
@jwt_required()
def create_wall():
    """Create a new wall from uploaded image or solid color."""
    user_id = int(get_jwt_identity())

    # Get form data
    name = request.form.get('name', 'Untitled Wall')
    description = request.form.get('description', '')
    width_cm = request.form.get('width_cm', type=float)
    height_cm = request.form.get('height_cm', type=float)
    background_color = request.form.get('background_color')

    image_path_val = None
    thumbnail_path_val = None
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'walls')
    os.makedirs(upload_folder, exist_ok=True)

    if 'image' in request.files and request.files['image'].filename != '':
        file = request.files['image']

        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400

        # Save the image
        filename = secure_filename(file.filename)
        unique_filename = f"{user_id}_{int(os.urandom(4).hex(), 16)}_{filename}"
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)

        # Process image and create thumbnail
        thumbnail_path = process_wall_image(file_path, upload_folder)

        image_path_val = f"walls/{unique_filename}"
        thumbnail_path_val = f"walls/{os.path.basename(thumbnail_path)}" if thumbnail_path else None
    elif background_color:
        # Generate a solid-color image for the wall
        hex_color = background_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        img = PILImage.new('RGB', (1920, 1080), rgb)
        unique_filename = f"{user_id}_{int(os.urandom(4).hex(), 16)}_color_wall.jpg"
        file_path = os.path.join(upload_folder, unique_filename)
        img.save(file_path, 'JPEG', quality=90)

        # Process image and create thumbnail
        thumbnail_path = process_wall_image(file_path, upload_folder)

        image_path_val = f"walls/{unique_filename}"
        thumbnail_path_val = f"walls/{os.path.basename(thumbnail_path)}" if thumbnail_path else None
    else:
        return jsonify({'error': 'Either an image or a background color is required'}), 400

    # Create wall record
    wall = Wall(
        user_id=user_id,
        name=name,
        description=description,
        image_path=image_path_val,
        thumbnail_path=thumbnail_path_val,
        background_color=background_color,
        width_cm=width_cm,
        height_cm=height_cm,
        scene_config={},
        frame_placements=[]
    )

    db.session.add(wall)
    db.session.commit()

    return jsonify({
        'message': 'Wall created successfully',
        'wall': wall.to_dict()
    }), 201


@bp.route('/<int:wall_id>', methods=['PUT'])
@jwt_required()
def update_wall(wall_id):
    """Update a wall's details or frame placements."""
    user_id = int(get_jwt_identity())
    wall = db.session.query(Wall).filter_by(id=wall_id, user_id=user_id).first()

    if not wall:
        return jsonify({'error': 'Wall not found'}), 404

    data = request.get_json()

    if 'name' in data:
        wall.name = data['name']
    if 'description' in data:
        wall.description = data['description']
    if 'width_cm' in data:
        wall.width_cm = data['width_cm']
    if 'height_cm' in data:
        wall.height_cm = data['height_cm']
    if 'background_color' in data:
        wall.background_color = data['background_color']
    if 'scene_config' in data:
        wall.scene_config = data['scene_config']
    if 'frame_placements' in data:
        wall.frame_placements = data['frame_placements']

    db.session.commit()

    return jsonify({
        'message': 'Wall updated',
        'wall': wall.to_dict()
    }), 200


@bp.route('/<int:wall_id>', methods=['DELETE'])
@jwt_required()
def delete_wall(wall_id):
    """Delete a wall."""
    user_id = int(get_jwt_identity())
    wall = db.session.query(Wall).filter_by(id=wall_id, user_id=user_id).first()

    if not wall:
        return jsonify({'error': 'Wall not found'}), 404

    # Delete associated files
    upload_folder = current_app.config['UPLOAD_FOLDER']
    if wall.image_path:
        try:
            os.remove(os.path.join(upload_folder, wall.image_path))
        except OSError:
            pass
    if wall.thumbnail_path:
        try:
            os.remove(os.path.join(upload_folder, wall.thumbnail_path))
        except OSError:
            pass

    db.session.delete(wall)
    db.session.commit()

    return jsonify({'message': 'Wall deleted'}), 200


@bp.route('/<int:wall_id>/placements', methods=['POST'])
@jwt_required()
def add_frame_placement(wall_id):
    """Add a frame placement to a wall."""
    user_id = int(get_jwt_identity())
    wall = db.session.query(Wall).filter_by(id=wall_id, user_id=user_id).first()

    if not wall:
        return jsonify({'error': 'Wall not found'}), 404

    data = request.get_json()

    placement = {
        'frame_id': data.get('frame_id'),
        'picture_id': data.get('picture_id'),
        'position': data.get('position', {'x': 0, 'y': 0, 'z': 0}),
        'rotation': data.get('rotation', {'x': 0, 'y': 0, 'z': 0}),
        'scale': data.get('scale', 1.0)
    }

    placements = list(wall.frame_placements or [])
    placements.append(placement)
    wall.frame_placements = placements
    flag_modified(wall, 'frame_placements')

    db.session.commit()

    return jsonify({
        'message': 'Frame placement added',
        'wall': wall.to_dict()
    }), 200
