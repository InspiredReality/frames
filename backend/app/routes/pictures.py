"""Picture routes for managing captured artwork images."""
import os
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from app import db
from app.models import Picture, PictureFrame
from app.services.image_processor import process_picture_image
from app.services.model_generator import generate_frame_model

bp = Blueprint('pictures', __name__)


@bp.before_request
def log_request():
    """Debug: Log all requests to this blueprint."""
    print(f"=== Pictures Blueprint Request ===")
    print(f"Method: {request.method}")
    print(f"Path: {request.path}")
    print(f"Headers: {dict(request.headers)}")
    auth = request.headers.get('Authorization', 'NONE')
    print(f"Auth header: {auth[:50]}..." if len(auth) > 50 else f"Auth header: {auth}")


def allowed_file(filename):
    """Check if file extension is allowed."""
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


@bp.route('', methods=['GET'])
@jwt_required()
def get_pictures():
    """Get all pictures for the current user."""
    user_id = int(get_jwt_identity())
    pictures = Picture.query.filter_by(user_id=user_id).order_by(Picture.created_at.desc()).all()

    return jsonify({
        'pictures': [p.to_dict(include_frames=True) for p in pictures]
    }), 200


@bp.route('/<int:picture_id>', methods=['GET'])
@jwt_required()
def get_picture(picture_id):
    """Get a specific picture by ID."""
    user_id = int(get_jwt_identity())
    picture = Picture.query.filter_by(id=picture_id, user_id=user_id).first()

    if not picture:
        return jsonify({'error': 'Picture not found'}), 404

    return jsonify({'picture': picture.to_dict(include_frames=True)}), 200


@bp.route('', methods=['POST'])
@jwt_required()
def create_picture():
    """Create a new picture from uploaded image."""
    print("=== create_picture called ===")
    try:
        user_id = int(get_jwt_identity())
        print(f"User ID from JWT: {user_id}")

        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400

        file = request.files['image']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400

        # Get form data
        name = request.form.get('name', 'Untitled Frame')
        description = request.form.get('description', '')
        wall_id = request.form.get('wall_id', type=int)  # Optional wall assignment

        # Save the image
        filename = secure_filename(file.filename)
        if not filename:
            filename = 'image.jpg'
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'frames')

        # Ensure upload folder exists
        os.makedirs(upload_folder, exist_ok=True)

        unique_filename = f"{user_id}_{int(os.urandom(4).hex(), 16)}_{filename}"
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)

        # Process image and get dimensions
        result = process_picture_image(file_path, upload_folder)

        # Create picture record (original_image_path preserves the initial capture)
        picture = Picture(
            user_id=user_id,
            wall_id=wall_id,
            name=name,
            description=description,
            image_path=f"frames/{unique_filename}",
            original_image_path=f"frames/{unique_filename}",
            thumbnail_path=f"frames/{os.path.basename(result['thumbnail_path'])}" if result.get('thumbnail_path') else None,
            width_px=result.get('width'),
            height_px=result.get('height')
        )

        db.session.add(picture)
        db.session.commit()

        return jsonify({
            'message': 'Picture created successfully',
            'picture': picture.to_dict()
        }), 201

    except Exception as e:
        import traceback
        print(f"Error creating picture: {e}")
        print(traceback.format_exc())
        db.session.rollback()
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@bp.route('/<int:picture_id>', methods=['PUT'])
@jwt_required()
def update_picture(picture_id):
    """Update a picture's details."""
    user_id = int(get_jwt_identity())
    picture = Picture.query.filter_by(id=picture_id, user_id=user_id).first()

    if not picture:
        return jsonify({'error': 'Picture not found'}), 404

    data = request.get_json()

    if 'name' in data:
        picture.name = data['name']
    if 'description' in data:
        picture.description = data['description']
    if 'wall_id' in data:
        picture.wall_id = data['wall_id']  # Can be None to unassign

    db.session.commit()

    return jsonify({
        'message': 'Picture updated',
        'picture': picture.to_dict()
    }), 200


@bp.route('/<int:picture_id>/image', methods=['PUT'])
@jwt_required()
def update_picture_image(picture_id):
    """Update a picture's image (for recrop functionality)."""
    user_id = int(get_jwt_identity())
    picture = Picture.query.filter_by(id=picture_id, user_id=user_id).first()

    if not picture:
        return jsonify({'error': 'Picture not found'}), 404

    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        frames_folder = os.path.join(upload_folder, 'frames')

        # Delete old cropped image files (but never the original)
        if picture.image_path and picture.image_path != picture.original_image_path:
            old_image = os.path.join(upload_folder, picture.image_path)
            if os.path.exists(old_image):
                os.remove(old_image)
        if picture.thumbnail_path:
            old_thumb = os.path.join(upload_folder, picture.thumbnail_path)
            if os.path.exists(old_thumb):
                os.remove(old_thumb)

        # Save new image
        filename = secure_filename(file.filename) or 'recropped.jpg'
        unique_filename = f"{user_id}_{int(os.urandom(4).hex(), 16)}_{filename}"
        file_path = os.path.join(frames_folder, unique_filename)
        file.save(file_path)

        # Process image and create new thumbnail
        result = process_picture_image(file_path, frames_folder)

        # Update picture record
        picture.image_path = f"frames/{unique_filename}"
        if result.get('thumbnail_path'):
            picture.thumbnail_path = f"frames/{os.path.basename(result['thumbnail_path'])}"
        picture.width_px = result.get('width')
        picture.height_px = result.get('height')

        db.session.commit()

        return jsonify({
            'message': 'Image updated successfully',
            'picture': picture.to_dict(include_frames=True)
        }), 200

    except Exception as e:
        import traceback
        print(f"Error updating picture image: {e}")
        print(traceback.format_exc())
        db.session.rollback()
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@bp.route('/<int:picture_id>', methods=['DELETE'])
@jwt_required()
def delete_picture(picture_id):
    """Delete a picture and all associated frames."""
    user_id = int(get_jwt_identity())
    picture = Picture.query.filter_by(id=picture_id, user_id=user_id).first()

    if not picture:
        return jsonify({'error': 'Picture not found'}), 404

    # Delete associated files
    upload_folder = current_app.config['UPLOAD_FOLDER']
    if picture.image_path:
        try:
            os.remove(os.path.join(upload_folder, picture.image_path))
        except OSError:
            pass
    if picture.thumbnail_path:
        try:
            os.remove(os.path.join(upload_folder, picture.thumbnail_path))
        except OSError:
            pass

    # Delete frame models
    for frame in picture.frames:
        if frame.model_path:
            try:
                os.remove(os.path.join(upload_folder, frame.model_path))
            except OSError:
                pass

    db.session.delete(picture)
    db.session.commit()

    return jsonify({'message': 'Picture deleted'}), 200


@bp.route('/<int:picture_id>/frames', methods=['POST'])
@jwt_required()
def create_frame(picture_id):
    """Create a 3D frame for a picture with specified dimensions."""
    try:
        user_id = int(get_jwt_identity())
        picture = Picture.query.filter_by(id=picture_id, user_id=user_id).first()

        if not picture:
            return jsonify({'error': 'Picture not found'}), 404

        data = request.get_json()

        # Validate dimensions
        unit = data.get('unit', 'inches')
        width = data.get('width')
        height = data.get('height')
        depth = data.get('depth', 1.0 if unit == 'inches' else 2.54)

        if not all([width, height]):
            return jsonify({'error': 'Width and height are required'}), 400

        # Create frame
        frame = PictureFrame(
            picture_id=picture.id,
            name=data.get('name', f'Frame {picture.frames.count() + 1}'),
            frame_color=data.get('frame_color', '#8B4513'),
            frame_material=data.get('frame_material', 'wood'),
            mat_width_inches=data.get('mat_width', 0),
            mat_color=data.get('mat_color', '#FFFFFF')
        )

        if unit == 'cm':
            frame.set_dimensions_cm(width, height, depth)
        else:
            frame.set_dimensions_inches(width, height, depth)

        db.session.add(frame)
        db.session.flush()  # Get the ID

        # Generate 3D model
        models_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'models')
        os.makedirs(models_folder, exist_ok=True)

        model_path = generate_frame_model(
            frame_id=frame.id,
            width_cm=frame.width_cm,
            height_cm=frame.height_cm,
            depth_cm=frame.depth_cm,
            output_folder=models_folder,
            picture_path=os.path.join(current_app.config['UPLOAD_FOLDER'], picture.image_path)
        )

        if model_path:
            frame.model_path = f"models/{os.path.basename(model_path)}"

        db.session.commit()

        return jsonify({
            'message': 'Frame created successfully',
            'frame': frame.to_dict()
        }), 201

    except Exception as e:
        import traceback
        print(f"Error creating frame: {e}")
        print(traceback.format_exc())
        db.session.rollback()
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@bp.route('/<int:picture_id>/frames/<int:frame_id>', methods=['PUT'])
@jwt_required()
def update_frame(picture_id, frame_id):
    """Update a frame's dimensions."""
    try:
        user_id = int(get_jwt_identity())
        picture = Picture.query.filter_by(id=picture_id, user_id=user_id).first()

        if not picture:
            return jsonify({'error': 'Picture not found'}), 404

        frame = PictureFrame.query.filter_by(id=frame_id, picture_id=picture_id).first()

        if not frame:
            return jsonify({'error': 'Frame not found'}), 404

        data = request.get_json()

        # Update dimensions if provided
        if 'width' in data and 'height' in data:
            unit = data.get('unit', 'cm')
            width = float(data['width'])
            height = float(data['height'])

            # Get depth with fallback defaults
            if unit == 'cm':
                depth = float(data.get('depth', frame.depth_cm if frame.depth_cm else 2.54))
            else:
                depth = float(data.get('depth', frame.depth_inches if frame.depth_inches else 1.0))

            if unit == 'cm':
                frame.set_dimensions_cm(width, height, depth)
            else:
                frame.set_dimensions_inches(width, height, depth)

        # Update styling if provided
        if 'frame_color' in data:
            frame.frame_color = data['frame_color']
        if 'frame_material' in data:
            frame.frame_material = data['frame_material']

        db.session.commit()

        return jsonify({
            'message': 'Frame updated',
            'frame': frame.to_dict()
        }), 200

    except Exception as e:
        import traceback
        print(f"Error updating frame: {e}")
        print(traceback.format_exc())
        db.session.rollback()
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@bp.route('/<int:picture_id>/frames/<int:frame_id>', methods=['DELETE'])
@jwt_required()
def delete_frame(picture_id, frame_id):
    """Delete a frame."""
    user_id = int(get_jwt_identity())
    picture = Picture.query.filter_by(id=picture_id, user_id=user_id).first()

    if not picture:
        return jsonify({'error': 'Picture not found'}), 404

    frame = PictureFrame.query.filter_by(id=frame_id, picture_id=picture_id).first()

    if not frame:
        return jsonify({'error': 'Frame not found'}), 404

    # Delete model file
    if frame.model_path:
        try:
            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], frame.model_path))
        except OSError:
            pass

    db.session.delete(frame)
    db.session.commit()

    return jsonify({'message': 'Frame deleted'}), 200
