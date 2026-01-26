"""Wall model for storing virtual wall configurations."""
from datetime import datetime
from app import db


class Wall(db.Model):
    """Wall model representing a captured wall with placed frames."""

    __tablename__ = 'walls'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

    # Wall image
    image_path = db.Column(db.String(500), nullable=False)
    thumbnail_path = db.Column(db.String(500))

    # Wall dimensions (estimated or user-provided)
    width_cm = db.Column(db.Float)
    height_cm = db.Column(db.Float)

    # 3D scene configuration (JSON)
    scene_config = db.Column(db.JSON, default=dict)

    # Placed frames configuration (JSON array of frame placements for AR)
    frame_placements = db.Column(db.JSON, default=list)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to pictures/frames assigned to this wall
    pictures = db.relationship('Picture', backref='wall', lazy='dynamic')

    def to_dict(self, include_placements=True, include_frames=False):
        """Serialize wall to dictionary."""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'image_path': self.image_path,
            'thumbnail_path': self.thumbnail_path,
            'width_cm': self.width_cm,
            'height_cm': self.height_cm,
            'scene_config': self.scene_config,
            'frame_count': self.pictures.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_placements:
            data['frame_placements'] = self.frame_placements
        if include_frames:
            data['frames'] = [p.to_dict(include_frames=True) for p in self.pictures]
        return data

    def __repr__(self):
        return f'<Wall {self.name}>'
