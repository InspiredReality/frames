"""Wall model for storing virtual wall configurations."""
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.db import Base


class Wall(Base):
    """Wall model representing a captured wall with placed frames."""

    __tablename__ = 'walls'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)

    # Wall image (nullable for color-only walls)
    image_path = Column(String(500), nullable=True)
    thumbnail_path = Column(String(500))
    background_color = Column(String(7))  # Hex color e.g. '#FFFFFF'

    # Wall dimensions (estimated or user-provided)
    width_cm = Column(Float)
    height_cm = Column(Float)

    # 3D scene configuration (JSON)
    scene_config = Column(JSON, default=dict)

    # Placed frames configuration (JSON array of frame placements for AR)
    frame_placements = Column(JSON, default=list)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to pictures/frames assigned to this wall
    pictures = relationship('Picture', backref='wall', lazy='dynamic')

    def to_dict(self, include_placements=True, include_frames=False):
        """Serialize wall to dictionary."""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'image_path': self.image_path,
            'thumbnail_path': self.thumbnail_path,
            'background_color': self.background_color,
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
