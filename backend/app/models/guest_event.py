"""Anonymous session activity tracking."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, Index

from app.db import Base


class GuestEvent(Base):
    __tablename__ = 'guest_events'

    id = Column(Integer, primary_key=True)
    session_id = Column(String(36), nullable=False)
    action = Column(String(50), nullable=False)
    event_metadata = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('ix_guest_events_session_id', 'session_id'),
        Index('ix_guest_events_created_at', 'created_at'),
    )
