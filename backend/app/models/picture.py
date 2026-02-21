"""Picture and PictureFrame models."""
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db import Base


class Picture(Base):
    """Picture model representing a captured artwork/photo."""

    __tablename__ = 'pictures'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    wall_id = Column(Integer, ForeignKey('walls.id'), nullable=True, index=True)  # Optional wall assignment
    name = Column(String(100), nullable=False)
    description = Column(Text)

    # Image paths
    image_path = Column(String(500), nullable=False)
    original_image_path = Column(String(500))  # Preserved original from capture
    thumbnail_path = Column(String(500))

    # Original image dimensions (pixels)
    width_px = Column(Integer)
    height_px = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to frames
    frames = relationship('PictureFrame', backref='picture', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self, include_frames=False):
        """Serialize picture to dictionary."""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'wall_id': self.wall_id,
            'name': self.name,
            'description': self.description,
            'image_path': self.image_path,
            'original_image_path': self.original_image_path,
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


class PictureFrame(Base):
    """PictureFrame model representing a 3D frame for a picture."""

    __tablename__ = 'picture_frames'

    id = Column(Integer, primary_key=True)
    picture_id = Column(Integer, ForeignKey('pictures.id'), nullable=False, index=True)
    name = Column(String(100))

    # Real-world dimensions
    width_inches = Column(Float, nullable=False)
    height_inches = Column(Float, nullable=False)
    depth_inches = Column(Float, default=1.0)

    # Metric dimensions (auto-calculated)
    width_cm = Column(Float, nullable=False)
    height_cm = Column(Float, nullable=False)
    depth_cm = Column(Float, default=2.54)

    # Total dimensions (picture + frame border)
    total_width_inches = Column(Float)
    total_height_inches = Column(Float)
    total_width_cm = Column(Float)
    total_height_cm = Column(Float)

    # Frame styling
    frame_color = Column(String(7), default='#8B4513')  # Brown default
    frame_material = Column(String(50), default='wood')
    mat_width_inches = Column(Float, default=0)  # Mat/border width
    mat_color = Column(String(7), default='#FFFFFF')

    # Generated 3D model path
    model_path = Column(String(500))
    model_format = Column(String(10), default='glb')

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    INCHES_TO_CM = 2.54

    def set_dimensions_inches(self, width, height, depth=1.0, total_width=None, total_height=None):
        """Set dimensions in inches and auto-calculate cm."""
        self.width_inches = width
        self.height_inches = height
        self.depth_inches = depth
        self.width_cm = width * self.INCHES_TO_CM
        self.height_cm = height * self.INCHES_TO_CM
        self.depth_cm = depth * self.INCHES_TO_CM
        if total_width is not None:
            self.total_width_inches = total_width
            self.total_width_cm = total_width * self.INCHES_TO_CM
        if total_height is not None:
            self.total_height_inches = total_height
            self.total_height_cm = total_height * self.INCHES_TO_CM

    def set_dimensions_cm(self, width, height, depth=2.54, total_width=None, total_height=None):
        """Set dimensions in cm and auto-calculate inches."""
        self.width_cm = width
        self.height_cm = height
        self.depth_cm = depth
        self.width_inches = width / self.INCHES_TO_CM
        self.height_inches = height / self.INCHES_TO_CM
        self.depth_inches = depth / self.INCHES_TO_CM
        if total_width is not None:
            self.total_width_cm = total_width
            self.total_width_inches = total_width / self.INCHES_TO_CM
        if total_height is not None:
            self.total_height_cm = total_height
            self.total_height_inches = total_height / self.INCHES_TO_CM

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
                    'depth': self.depth_inches,
                    'total_width': self.total_width_inches,
                    'total_height': self.total_height_inches
                },
                'cm': {
                    'width': self.width_cm,
                    'height': self.height_cm,
                    'depth': self.depth_cm,
                    'total_width': self.total_width_cm,
                    'total_height': self.total_height_cm
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
