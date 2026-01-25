"""3D model routes for serving and managing generated models."""
import os
from flask import Blueprint, send_from_directory, current_app, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import PictureFrame, Picture

bp = Blueprint('models3d', __name__)


@bp.route('/<int:frame_id>', methods=['GET'])
@jwt_required()
def get_model(frame_id):
    """Get the 3D model file for a frame."""
    user_id = get_jwt_identity()

    frame = PictureFrame.query.get(frame_id)
    if not frame:
        return jsonify({'error': 'Frame not found'}), 404

    # Verify ownership
    picture = Picture.query.get(frame.picture_id)
    if not picture or picture.user_id != user_id:
        return jsonify({'error': 'Access denied'}), 403

    if not frame.model_path:
        return jsonify({'error': 'Model not generated'}), 404

    upload_folder = current_app.config['UPLOAD_FOLDER']
    model_dir = os.path.dirname(os.path.join(upload_folder, frame.model_path))
    model_file = os.path.basename(frame.model_path)

    return send_from_directory(model_dir, model_file)


@bp.route('/<int:frame_id>/info', methods=['GET'])
@jwt_required()
def get_model_info(frame_id):
    """Get information about a 3D model."""
    user_id = get_jwt_identity()

    frame = PictureFrame.query.get(frame_id)
    if not frame:
        return jsonify({'error': 'Frame not found'}), 404

    # Verify ownership
    picture = Picture.query.get(frame.picture_id)
    if not picture or picture.user_id != user_id:
        return jsonify({'error': 'Access denied'}), 403

    return jsonify({
        'frame': frame.to_dict(),
        'picture': picture.to_dict(include_frames=False)
    }), 200


@bp.route('/uploads/<path:filename>', methods=['GET'])
def serve_upload(filename):
    """Serve uploaded files (images, models, etc.)."""
    upload_folder = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_folder, filename)
