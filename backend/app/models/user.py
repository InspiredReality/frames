"""User model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

from app.db import Base


class User(Base):
    """User model for authentication and ownership."""

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    walls = relationship('Wall', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    pictures = relationship('Picture', backref='owner', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify the password against the hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Serialize user to dictionary."""
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'is_admin': self.is_admin if self.is_admin is not None else False,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<User {self.username}>'
