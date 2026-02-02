from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import FileResponse

from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db import get_db
from app.models import PictureFrame, Picture, User
from app.routers.auth import get_current_user

router = APIRouter()


def _resolve_safe_upload_path(filename: str) -> Path:
    """
    Prevent path traversal: only allow paths inside UPLOAD_FOLDER.
    """
    root = Path(settings.UPLOAD_FOLDER).resolve()
    target = (root / filename).resolve()
    if root not in target.parents and target != root:
        raise HTTPException(status_code=400, detail="Invalid filename")
    return target


@router.get("/{frame_id}", status_code=200)
def get_model(
    frame_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    frame = db.get(PictureFrame, frame_id)
    if not frame:
        raise HTTPException(status_code=404, detail="Frame not found")

    picture = db.get(Picture, frame.picture_id)
    if not picture or picture.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if not frame.model_path:
        raise HTTPException(status_code=404, detail="Model not generated")

    model_path = _resolve_safe_upload_path(frame.model_path)
    if not model_path.exists():
        raise HTTPException(status_code=404, detail="Model file missing")

    # If you know the real mime type (e.g., model/gltf+json, model/gltf-binary, application/octet-stream),
    # you can set media_type. We'll default to octet-stream for safety.
    return FileResponse(
        path=str(model_path),
        media_type="application/octet-stream",
        filename=model_path.name,
    )


@router.get("/{frame_id}/info", status_code=200)
def get_model_info(
    frame_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    frame = db.get(PictureFrame, frame_id)
    if not frame:
        raise HTTPException(status_code=404, detail="Frame not found")

    picture = db.get(Picture, frame.picture_id)
    if not picture or picture.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "frame": frame.to_dict(),
        "picture": picture.to_dict(include_frames=False),
    }


@router.get("/uploads/{filename:path}", status_code=200)
def serve_upload(filename: str, response: Response):
    """
    Serve uploaded files (images, models, etc.).
    Public endpoint in your Flask version.
    """
    file_path = _resolve_safe_upload_path(filename)
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    # Add headers similar to Flask version
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"

    return FileResponse(path=str(file_path))
