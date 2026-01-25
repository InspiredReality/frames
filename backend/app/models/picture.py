"""Picture and PictureFrame models."""
from datetime import datetime
from app import db


class Picture(db.Model):
    """Picture model representing a captured artwork/photo."""

    __tablename__ = 'pictures'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

    # Image paths
    image_path = db.Column(db.String(500), nullable=False)
    thumbnail_path = db.Column(db.String(500))

    # Original image dimensions (pixels)
    width_px = db.Column(db.Integer)
    height_px = db.Column(db.Integer)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to frames
    frames = db.relationship('PictureFrame', backref='picture', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self, include_frames=False):
        """Serialize picture to dictionary."""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'image_path': self.image_path,
            'thumbnail_path': self.thumbnail_path,
            'width_px': self.width_px,
            'height_px': self.height_px,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_frames:
            data['frames'] = [f.to_dict() for f in self.frames]
        return data

    def __repr__(self):
        return f'<Picture {self.name}>'


class PictureFrame(db.Model):
    """PictureFrame model representing a 3D frame for a picture."""

    __tablename__ = 'picture_frames'

    id = db.Column(db.Integer, primary_key=True)
    picture_id = db.Column(db.Integer, db.ForeignKey('pictures.id'), nullable=False, index=True)
    name = db.Column(db.String(100))

    # Real-world dimensions
    width_inches = db.Column(db.Float, nullable=False)
    height_inches = db.Column(db.Float, nullable=False)
    depth_inches = db.Column(db.Float, default=1.0)

    # Metric dimensions (auto-calculated)
    width_cm = db.Column(db.Float, nullable=False)
    height_cm = db.Column(db.Float, nullable=False)
    depth_cm = db.Column(db.Float, default=2.54)

    # Frame styling
    frame_color = db.Column(db.String(7), default='#8B4513')  # Brown default
    frame_material = db.Column(db.String(50), default='wood')
    mat_width_inches = db.Column(db.Float, default=0)  # Mat/border width
    mat_color = db.Column(db.String(7), default='#FFFFFF')

    # Generated 3D model path
    model_path = db.Column(db.String(500))
    model_format = db.Column(db.String(10), default='glb')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    INCHES_TO_CM = 2.54

    def set_dimensions_inches(self, width, height, depth=1.0):
        """Set dimensions in inches and auto-calculate cm."""
        self.width_inches = width
        self.height_inches = height
        self.depth_inches = depth
        self.width_cm = width * self.INCHES_TO_CM
        self.height_cm = height * self.INCHES_TO_CM
        self.depth_cm = depth * self.INCHES_TO_CM

    def set_dimensions_cm(self, width, height, depth=2.54):
        """Set dimensions in cm and auto-calculate inches."""
        self.width_cm = width
        self.height_cm = height
        self.depth_cm = depth
        self.width_inches = width / self.INCHES_TO_CM
        self.height_inches = height / self.INCHES_TO_CM
        self.depth_inches = depth / self.INCHES_TO_CM

    def to_dict(self):
        """Serialize frame to dictionary."""
        return {
            'id': self.id,
            'picture_id': self.picture_id,
            'name': self.name,
            'dimensions': {
                'inches': {
                    'width': self.width_inches,
                    'height': self.height_inches,
                    'depth': self.depth_inches
                },
                'cm': {
                    'width': self.width_cm,
                    'height': self.height_cm,
                    'depth': self.depth_cm
                }
            },
            'styling': {
                'frame_color': self.frame_color,
                'frame_material': self.frame_material,
                'mat_width_inches': self.mat_width_inches,
                'mat_color': self.mat_color
            },
            'model_path': self.model_path,
            'model_format': self.model_format,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<PictureFrame {self.id} ({self.width_inches}x{self.height_inches} in)>'
