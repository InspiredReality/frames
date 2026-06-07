"""Admin-only endpoints for user management and content moderation."""
from typing import List
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.core.settings import settings
from app.models import User, Wall, Picture
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
