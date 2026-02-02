import os
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, EmailStr, Field

from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db import get_db
from app.models import Picture, PictureFrame, User
from app.routers.auth import get_current_user
from app.services.image_processor import process_picture_image
from app.services.model_generator import generate_frame_model
from app.utils.uploads import make_safe_filename, save_upload_with_limit, verify_image_file

router = APIRouter()


# ----------------------------
# Schemas
# ----------------------------
class PictureUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    wall_id: Optional[int] = None  # can be None to unassign


class FrameCreateRequest(BaseModel):
    unit: str = Field(default="inches", pattern="^(inches|cm)$")
    width: float
    height: float
    depth: Optional[float] = None

    name: Optional[str] = None
    frame_color: str = Field(default="#8B4513")
    frame_material: str = Field(default="wood")
    mat_width: float = Field(default=0)
    mat_color: str = Field(default="#FFFFFF")


class FrameUpdateRequest(BaseModel):
    unit: str = Field(default="cm", pattern="^(inches|cm)$")
    width: Optional[float] = None
    height: Optional[float] = None
    depth: Optional[float] = None

    frame_color: Optional[str] = None
    frame_material: Optional[str] = None


# ----------------------------
# Helpers
# ----------------------------
def _safe_unlink(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except TypeError:
        # Python <3.8 fallback not needed for you, but safe anyway
        try:
            if path.exists():
                path.unlink()
        except Exception:
            pass


# ----------------------------
# Routes
# ----------------------------
@router.get("", status_code=200)
def get_pictures(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pictures = (
        db.query(Picture)
        .filter(Picture.user_id == current_user.id)
        .order_by(Picture.created_at.desc())
        .all()
    )
    return {"pictures": [p.to_dict(include_frames=True) for p in pictures]}


@router.get("/{picture_id}", status_code=200)
def get_picture(
    picture_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    picture = (
        db.query(Picture)
        .filter(Picture.id == picture_id, Picture.user_id == current_user.id)
        .first()
    )
    if not picture:
        raise HTTPException(status_code=404, detail="Picture not found")

    return {"picture": picture.to_dict(include_frames=True)}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_picture(
    # multipart/form-data
    name: str = Form("Untitled Frame"),
    description: str = Form(""),
    wall_id: Optional[int] = Form(None),

    image: UploadFile = File(...),

    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate file presence
    if not image.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    frames_folder = Path(settings.UPLOAD_FOLDER) / "frames"
    frames_folder.mkdir(parents=True, exist_ok=True)

    # Save upload securely
    safe_name = make_safe_filename(current_user.id, image.filename)
    file_path = frames_folder / safe_name

    await save_upload_with_limit(image, file_path)
    verify_image_file(file_path)

    try:
        # Process image and get dimensions/thumb
        result: Dict[str, Any] = process_picture_image(str(file_path), str(frames_folder))

        thumb = result.get("thumbnail_path")
        thumb_rel = f"frames/{os.path.basename(thumb)}" if thumb else None

        picture = Picture(
            user_id=current_user.id,
            wall_id=wall_id,
            name=name,
            description=description,
            image_path=f"frames/{safe_name}",
            original_image_path=f"frames/{safe_name}",
            thumbnail_path=thumb_rel,
            width_px=result.get("width"),
            height_px=result.get("height"),
        )

        db.add(picture)
        db.commit()
        db.refresh(picture)

        return {"message": "Picture created successfully", "picture": picture.to_dict()}

    except Exception as e:
        db.rollback()
        # If processing failed, remove the saved file
        _safe_unlink(file_path)
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@router.put("/{picture_id}", status_code=200)
def update_picture(
    picture_id: int,
    payload: PictureUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    picture = (
        db.query(Picture)
        .filter(Picture.id == picture_id, Picture.user_id == current_user.id)
        .first()
    )
    if not picture:
        raise HTTPException(status_code=404, detail="Picture not found")

    data = payload.model_dump(exclude_unset=True)

    if "name" in data:
        picture.name = data["name"]
    if "description" in data:
        picture.description = data["description"]
    if "wall_id" in data:
        picture.wall_id = data["wall_id"]  # can be None

    db.commit()
    db.refresh(picture)

    return {"message": "Picture updated", "picture": picture.to_dict()}


@router.put("/{picture_id}/image", status_code=200)
async def update_picture_image(
    picture_id: int,
    image: UploadFile = File(...),

    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    picture = (
        db.query(Picture)
        .filter(Picture.id == picture_id, Picture.user_id == current_user.id)
        .first()
    )
    if not picture:
        raise HTTPException(status_code=404, detail="Picture not found")

    if not image.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    upload_root = Path(settings.UPLOAD_FOLDER)
    frames_folder = upload_root / "frames"
    frames_folder.mkdir(parents=True, exist_ok=True)

    # Delete old cropped image files (but never the original)
    if picture.image_path and picture.image_path != picture.original_image_path:
        _safe_unlink(upload_root / picture.image_path)
    if picture.thumbnail_path:
        _safe_unlink(upload_root / picture.thumbnail_path)

    # Save new cropped image
    safe_name = make_safe_filename(current_user.id, image.filename)
    file_path = frames_folder / safe_name

    await save_upload_with_limit(image, file_path)
    verify_image_file(file_path)

    try:
        result: Dict[str, Any] = process_picture_image(str(file_path), str(frames_folder))

        picture.image_path = f"frames/{safe_name}"

        thumb = result.get("thumbnail_path")
        if thumb:
            picture.thumbnail_path = f"frames/{os.path.basename(thumb)}"

        picture.width_px = result.get("width")
        picture.height_px = result.get("height")

        db.commit()
        db.refresh(picture)

        return {"message": "Image updated successfully", "picture": picture.to_dict(include_frames=True)}

    except Exception as e:
        db.rollback()
        _safe_unlink(file_path)
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@router.delete("/{picture_id}", status_code=200)
def delete_picture(
    picture_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    picture = (
        db.query(Picture)
        .filter(Picture.id == picture_id, Picture.user_id == current_user.id)
        .first()
    )
    if not picture:
        raise HTTPException(status_code=404, detail="Picture not found")

    upload_root = Path(settings.UPLOAD_FOLDER)

    # Delete picture files
    if picture.image_path:
        _safe_unlink(upload_root / picture.image_path)
    if picture.thumbnail_path:
        _safe_unlink(upload_root / picture.thumbnail_path)

    # Delete frame model files
    # Assumes relationship picture.frames exists and is loaded lazily; iterating triggers load.
    for frame in list(picture.frames or []):
        if frame.model_path:
            _safe_unlink(upload_root / frame.model_path)

    db.delete(picture)
    db.commit()

    return {"message": "Picture deleted"}


@router.post("/{picture_id}/frames", status_code=status.HTTP_201_CREATED)
def create_frame(
    picture_id: int,
    payload: FrameCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    picture = (
        db.query(Picture)
        .filter(Picture.id == picture_id, Picture.user_id == current_user.id)
        .first()
    )
    if not picture:
        raise HTTPException(status_code=404, detail="Picture not found")

    # Defaults copied from Flask logic
    unit = payload.unit
    depth = payload.depth
    if depth is None:
        depth = 1.0 if unit == "inches" else 2.54

    # Create frame
    # NOTE: your Flask used picture.frames.count() for name. In SQLAlchemy we can derive count cheaply:
    existing_count = db.query(PictureFrame).filter(PictureFrame.picture_id == picture.id).count()

    frame = PictureFrame(
        picture_id=picture.id,
        name=payload.name or f"Frame {existing_count + 1}",
        frame_color=payload.frame_color,
        frame_material=payload.frame_material,
        mat_width_inches=payload.mat_width,
        mat_color=payload.mat_color,
    )

    if unit == "cm":
        frame.set_dimensions_cm(payload.width, payload.height, depth)
    else:
        frame.set_dimensions_inches(payload.width, payload.height, depth)

    db.add(frame)
    db.flush()  # get frame.id without committing yet

    # Generate 3D model
    models_folder = Path(settings.UPLOAD_FOLDER) / "models"
    models_folder.mkdir(parents=True, exist_ok=True)

    picture_abs = Path(settings.UPLOAD_FOLDER) / picture.image_path

    try:
        model_path = generate_frame_model(
            frame_id=frame.id,
            width_cm=frame.width_cm,
            height_cm=frame.height_cm,
            depth_cm=frame.depth_cm,
            output_folder=str(models_folder),
            picture_path=str(picture_abs),
        )
        if model_path:
            frame.model_path = f"models/{os.path.basename(model_path)}"

        db.commit()
        db.refresh(frame)

        return {"message": "Frame created successfully", "frame": frame.to_dict()}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@router.put("/{picture_id}/frames/{frame_id}", status_code=200)
def update_frame(
    picture_id: int,
    frame_id: int,
    payload: FrameUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    picture = (
        db.query(Picture)
        .filter(Picture.id == picture_id, Picture.user_id == current_user.id)
        .first()
    )
    if not picture:
        raise HTTPException(status_code=404, detail="Picture not found")

    frame = (
        db.query(PictureFrame)
        .filter(PictureFrame.id == frame_id, PictureFrame.picture_id == picture_id)
        .first()
    )
    if not frame:
        raise HTTPException(status_code=404, detail="Frame not found")

    data = payload.model_dump(exclude_unset=True)

    # Update dimensions if provided
    if data.get("width") is not None and data.get("height") is not None:
        unit = data.get("unit", "cm")
        width = float(data["width"])
        height = float(data["height"])

        if unit == "cm":
            depth = float(data.get("depth", frame.depth_cm if frame.depth_cm else 2.54))
            frame.set_dimensions_cm(width, height, depth)
        else:
            depth = float(data.get("depth", frame.depth_inches if frame.depth_inches else 1.0))
            frame.set_dimensions_inches(width, height, depth)

    # Update styling if provided
    if data.get("frame_color") is not None:
        frame.frame_color = data["frame_color"]
    if data.get("frame_material") is not None:
        frame.frame_material = data["frame_material"]

    db.commit()
    db.refresh(frame)

    return {"message": "Frame updated", "frame": frame.to_dict()}


@router.delete("/{picture_id}/frames/{frame_id}", status_code=200)
def delete_frame(
    picture_id: int,
    frame_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    picture = (
        db.query(Picture)
        .filter(Picture.id == picture_id, Picture.user_id == current_user.id)
        .first()
    )
    if not picture:
        raise HTTPException(status_code=404, detail="Picture not found")

    frame = (
        db.query(PictureFrame)
        .filter(PictureFrame.id == frame_id, PictureFrame.picture_id == picture_id)
        .first()
    )
    if not frame:
        raise HTTPException(status_code=404, detail="Frame not found")

    upload_root = Path(settings.UPLOAD_FOLDER)
    if frame.model_path:
        _safe_unlink(upload_root / frame.model_path)

    db.delete(frame)
    db.commit()

    return {"message": "Frame deleted"}
