"""Admin-only endpoints for user management and content moderation."""
from collections import defaultdict
from typing import List
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.core.settings import settings
from app.models import User, Wall, Picture
from app.models.guest_event import GuestEvent
from app.routers.auth import get_admin_user
from app.utils.uploads import _safe_unlink  # reuse existing helper if available

router = APIRouter()

GUEST_USER_EMAIL = "guest@frames.internal"


def _safe_unlink_path(path_str):
    if not path_str:
        return
    try:
        Path(path_str).unlink(missing_ok=True)
    except Exception:
        pass


# ----------------------------
# Users
# ----------------------------

@router.get("/users", status_code=200)
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    """List all non-guest users with wall/frame counts and last login."""
    users = (
        db.query(User)
        .filter(User.email != GUEST_USER_EMAIL)
        .order_by(User.created_at.desc())
        .all()
    )
    result = []
    for u in users:
        wall_count = u.walls.count()
        frame_count = u.pictures.count()
        data = u.to_dict()
        data["wall_count"] = wall_count
        data["frame_count"] = frame_count
        result.append(data)
    return {"users": result}


@router.get("/users/{user_id}", status_code=200)
def get_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    """Get a user with their full list of walls and frames."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    walls = (
        db.query(Wall)
        .filter(Wall.user_id == user_id)
        .order_by(Wall.created_at.desc())
        .all()
    )
    pictures = (
        db.query(Picture)
        .filter(Picture.user_id == user_id)
        .order_by(Picture.created_at.desc())
        .all()
    )

    return {
        "user": user.to_dict(),
        "walls": [w.to_dict(include_placements=False) for w in walls],
        "frames": [p.to_dict(include_frames=False) for p in pictures],
    }


# ----------------------------
# Guest sessions
# ----------------------------

@router.get("/guest-sessions", status_code=200)
def list_guest_sessions(
    db: Session = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    """Return all anonymous sessions with their event timelines, newest first."""
    events = (
        db.query(GuestEvent)
        .order_by(GuestEvent.session_id, GuestEvent.created_at)
        .all()
    )

    sessions_map = defaultdict(lambda: {"events": [], "first_seen": None, "last_seen": None})
    for ev in events:
        s = sessions_map[ev.session_id]
        s["events"].append({
            "action": ev.action,
            "metadata": ev.event_metadata,
            "created_at": ev.created_at.isoformat() if ev.created_at else None,
        })
        if s["first_seen"] is None or ev.created_at < s["first_seen"]:
            s["first_seen"] = ev.created_at
        if s["last_seen"] is None or ev.created_at > s["last_seen"]:
            s["last_seen"] = ev.created_at

    sessions = []
    for sid, data in sessions_map.items():
        counts = defaultdict(int)
        for ev in data["events"]:
            counts[ev["action"]] += 1
        sessions.append({
            "session_id": sid,
            "first_seen": data["first_seen"].isoformat() if data["first_seen"] else None,
            "last_seen": data["last_seen"].isoformat() if data["last_seen"] else None,
            "event_counts": dict(counts),
            "events": data["events"],
        })

    sessions.sort(key=lambda s: s["last_seen"] or "", reverse=True)
    return {"sessions": sessions}
