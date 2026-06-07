"""Endpoint for logging anonymous user activity events."""
import re
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional

from app.db import get_db
from app.models.guest_event import GuestEvent

router = APIRouter()

VALID_ACTIONS = {
    "wall_created",
    "frame_created",
    "frame_added_to_wall",
    "frame_rearranged",
    "layout_saved",
}

UUID_RE = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)


class GuestEventPayload(BaseModel):
    session_id: str
    action: str
    metadata: Optional[Dict[str, Any]] = None

    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v):
        if not UUID_RE.match(v):
            raise ValueError("Invalid session_id")
        return v

    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        if v not in VALID_ACTIONS:
            raise ValueError(f"Unknown action: {v}")
        return v


@router.post("", status_code=201)
def log_guest_event(
    payload: GuestEventPayload,
    db: Session = Depends(get_db),
):
    event = GuestEvent(
        session_id=payload.session_id,
        action=payload.action,
        event_metadata=payload.metadata,
        created_at=datetime.utcnow(),
    )
    db.add(event)
    db.commit()
    return {"ok": True}
