import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel, Field
from PIL import Image as PILImage

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.core.settings import settings
from app.db import get_db
from app.models import Wall, User
from app.routers.auth import get_current_user  # reuse auth dependency
from app.services.image_processor import process_wall_image

router = APIRouter()

DEFAULT_ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in DEFAULT_ALLOWED_EXTENSIONS


def _rand_suffix() -> str:
    # small, safe unique suffix (similar spirit to your os.urandom approach)
    return os.urandom(4).hex()


# ----------------------------
# Schemas
# ----------------------------
class WallUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    width_cm: Optional[float] = None
    height_cm: Optional[float] = None
    background_color: Optional[str] = None
    scene_config: Optional[Dict[str, Any]] = None
    frame_placements: Optional[List[Dict[str, Any]]] = None


class PlacementRequest(BaseModel):
    frame_id: Optional[int] = None
    picture_id: Optional[int] = None
    position: Dict[str, Any] = Field(default_factory=lambda: {"x": 0, "y": 0, "z": 0})
    rotation: Dict[str, Any] = Field(default_factory=lambda: {"x": 0, "y": 0, "z": 0})
    scale: float = 1.0


# ----------------------------
# Routes
# ----------------------------
@router.get("", status_code=200)
def get_walls(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    walls = (
        db.query(Wall)
        .filter(Wall.user_id == current_user.id)
        .order_by(Wall.created_at.desc())
        .all()
    )
    return {"walls": [w.to_dict(include_placements=True) for w in walls]}


@router.get("/{wall_id}", status_code=200)
def get_wall(
    wall_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wall = (
        db.query(Wall)
        .filter(Wall.id == wall_id, Wall.user_id == current_user.id)
        .first()
    )
    if not wall:
        raise HTTPException(status_code=404, detail="Wall not found")

    return {"wall": wall.to_dict(include_frames=True)}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_wall(
    # multipart/form-data fields
    name: str = Form("Untitled Wall"),
    description: str = Form(""),
    width_cm: Optional[float] = Form(None),
    height_cm: Optional[float] = Form(None),
    background_color: Optional[str] = Form(None),

    # file field (optional)
    image: Optional[UploadFile] = File(None),

    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    upload_folder = Path(settings.UPLOAD_FOLDER) / "walls"
    upload_folder.mkdir(parents=True, exist_ok=True)

    image_path_val: Optional[str] = None
    thumbnail_path_val: Optional[str] = None

    if image is not None and image.filename:
        if not allowed_file(image.filename):
            raise HTTPException(status_code=400, detail="File type not allowed")

        safe_name = os.path.basename(image.filename)  # simple safety; ok to tighten later
        unique_filename = f"{current_user.id}_{_rand_suffix()}_{safe_name}"
        file_path = upload_folder / unique_filename

        # Save uploaded file
        with open(file_path, "wb") as f:
            f.write(await image.read())

        # Process image and create thumbnail
        thumbnail_path = process_wall_image(str(file_path), str(upload_folder))

        image_path_val = f"walls/{unique_filename}"
        thumbnail_path_val = (
            f"walls/{os.path.basename(thumbnail_path)}" if thumbnail_path else None
        )

    elif background_color:
        # Generate a solid-color image for the wall
        hex_color = background_color.lstrip("#")
        if len(hex_color) != 6:
            raise HTTPException(status_code=400, detail="background_color must be a 6-digit hex color")

        try:
            rgb = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
        except ValueError:
            raise HTTPException(status_code=400, detail="background_color must be a valid hex color")

        img = PILImage.new("RGB", (1920, 1080), rgb)
        unique_filename = f"{current_user.id}_{_rand_suffix()}_color_wall.jpg"
        file_path = upload_folder / unique_filename
        img.save(file_path, "JPEG", quality=90)

        thumbnail_path = process_wall_image(str(file_path), str(upload_folder))

        image_path_val = f"walls/{unique_filename}"
        thumbnail_path_val = (
            f"walls/{os.path.basename(thumbnail_path)}" if thumbnail_path else None
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Either an image or a background color is required",
        )

    wall = Wall(
        user_id=current_user.id,
        name=name,
        description=description,
        image_path=image_path_val,
        thumbnail_path=thumbnail_path_val,
        background_color=background_color,
        width_cm=width_cm,
        height_cm=height_cm,
        scene_config={},
        frame_placements=[],
    )

    db.add(wall)
    db.commit()
    db.refresh(wall)

    return {"message": "Wall created successfully", "wall": wall.to_dict()}


@router.put("/{wall_id}", status_code=200)
def update_wall(
    wall_id: int,
    payload: WallUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wall = (
        db.query(Wall)
        .filter(Wall.id == wall_id, Wall.user_id == current_user.id)
        .first()
    )
    if not wall:
        raise HTTPException(status_code=404, detail="Wall not found")

    data = payload.model_dump(exclude_unset=True)

    for field in ("name", "description", "width_cm", "height_cm", "background_color", "scene_config"):
        if field in data:
            setattr(wall, field, data[field])

    if "frame_placements" in data:
        wall.frame_placements = data["frame_placements"]
        flag_modified(wall, "frame_placements")

    db.commit()
    db.refresh(wall)

    return {"message": "Wall updated", "wall": wall.to_dict()}


@router.delete("/{wall_id}", status_code=200)
def delete_wall(
    wall_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wall = (
        db.query(Wall)
        .filter(Wall.id == wall_id, Wall.user_id == current_user.id)
        .first()
    )
    if not wall:
        raise HTTPException(status_code=404, detail="Wall not found")

    # delete files
    upload_root = Path(settings.UPLOAD_FOLDER)
    if wall.image_path:
        try:
            (upload_root / wall.image_path).unlink(missing_ok=True)
        except TypeError:
            # py<3.8 compatibility not needed, but just in case
            try:
                os.remove(upload_root / wall.image_path)
            except OSError:
                pass

    if wall.thumbnail_path:
        try:
            (upload_root / wall.thumbnail_path).unlink(missing_ok=True)
        except TypeError:
            try:
                os.remove(upload_root / wall.thumbnail_path)
            except OSError:
                pass

    db.delete(wall)
    db.commit()

    return {"message": "Wall deleted"}


@router.post("/{wall_id}/placements", status_code=200)
def add_frame_placement(
    wall_id: int,
    payload: PlacementRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wall = (
        db.query(Wall)
        .filter(Wall.id == wall_id, Wall.user_id == current_user.id)
        .first()
    )
    if not wall:
        raise HTTPException(status_code=404, detail="Wall not found")

    placement = {
        "frame_id": payload.frame_id,
        "picture_id": payload.picture_id,
        "position": payload.position,
        "rotation": payload.rotation,
        "scale": payload.scale,
    }

    placements = list(wall.frame_placements or [])
    placements.append(placement)
    wall.frame_placements = placements
    flag_modified(wall, "frame_placements")

    db.commit()
    db.refresh(wall)

    return {"message": "Frame placement added", "wall": wall.to_dict()}
