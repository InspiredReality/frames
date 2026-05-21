"""Realities router — CRUD for Reality and top-level OrgOb operations."""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db import get_db
from app.models import User
from app.models.reality import Reality
from app.models.org_ob import OrgOb
from app.routers.auth import get_current_user
from app.services.image_processor import process_wall_image
from app.utils.uploads import make_safe_filename, save_upload_with_limit

router = APIRouter()


# ----------------------------
# Schemas
# ----------------------------
class RealityCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    meta: Optional[Dict[str, Any]] = Field(default_factory=dict)


class RealityUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class OrgObCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    meta: Optional[Dict[str, Any]] = Field(default_factory=dict)
    order_index: int = 0


# ----------------------------
# Reality routes
# ----------------------------
@router.get("", status_code=200)
def list_realities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    realities = (
        db.query(Reality)
        .filter(Reality.user_id == current_user.id)
        .order_by(Reality.created_at.desc())
        .all()
    )
    return {"realities": [r.to_dict() for r in realities]}


@router.post("", status_code=201)
def create_reality(
    payload: RealityCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reality = Reality(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
        meta=payload.meta or {},
    )
    db.add(reality)
    db.commit()
    db.refresh(reality)
    return {"message": "Reality created", "reality": reality.to_dict()}


@router.get("/{reality_id}", status_code=200)
def get_reality(
    reality_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reality = db.query(Reality).filter_by(id=reality_id, user_id=current_user.id).first()
    if not reality:
        raise HTTPException(status_code=404, detail="Reality not found")
    return {"reality": reality.to_dict()}


@router.put("/{reality_id}", status_code=200)
def update_reality(
    reality_id: int,
    payload: RealityUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reality = db.query(Reality).filter_by(id=reality_id, user_id=current_user.id).first()
    if not reality:
        raise HTTPException(status_code=404, detail="Reality not found")
    if payload.name is not None:
        reality.name = payload.name
    if payload.description is not None:
        reality.description = payload.description
    if payload.meta is not None:
        reality.meta = payload.meta
    db.commit()
    db.refresh(reality)
    return {"message": "Reality updated", "reality": reality.to_dict()}


@router.post("/{reality_id}/image", status_code=200)
async def upload_reality_image(
    reality_id: int,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reality = db.query(Reality).filter_by(id=reality_id, user_id=current_user.id).first()
    if not reality:
        raise HTTPException(status_code=404, detail="Reality not found")

    upload_folder = Path(settings.UPLOAD_FOLDER) / "realities"
    upload_folder.mkdir(parents=True, exist_ok=True)
    upload_root = Path(settings.UPLOAD_FOLDER)

    if not image.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    safe_name = make_safe_filename(current_user.id, image.filename)
    file_path = upload_folder / safe_name

    # Delete old image if present
    if reality.image_path:
        try:
            (upload_root / reality.image_path).unlink(missing_ok=True)
        except Exception:
            pass

    await save_upload_with_limit(image, file_path)

    # Resize large images and generate thumbnail (reuse wall image processor)
    process_wall_image(str(file_path), str(upload_folder))

    reality.image_path = f"realities/{safe_name}"
    db.commit()
    db.refresh(reality)
    return {"message": "Image uploaded", "reality": reality.to_dict()}


@router.delete("/{reality_id}", status_code=200)
def delete_reality(
    reality_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reality = db.query(Reality).filter_by(id=reality_id, user_id=current_user.id).first()
    if not reality:
        raise HTTPException(status_code=404, detail="Reality not found")
    db.delete(reality)
    db.commit()
    return {"message": "Reality deleted"}


# ----------------------------
# OrgOb routes nested under a Reality
# ----------------------------
@router.get("/{reality_id}/org-obs", status_code=200)
def list_top_level_org_obs(
    reality_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return top-level OrgObs (parent_id IS NULL) with their children embedded."""
    reality = db.query(Reality).filter_by(id=reality_id, user_id=current_user.id).first()
    if not reality:
        raise HTTPException(status_code=404, detail="Reality not found")

    top_level = (
        db.query(OrgOb)
        .filter(OrgOb.reality_id == reality_id, OrgOb.parent_id == None)  # noqa: E711
        .order_by(OrgOb.order_index)
        .all()
    )
    return {"org_obs": [o.to_dict(include_children=True) for o in top_level]}


@router.post("/{reality_id}/org-obs", status_code=201)
def create_org_ob(
    reality_id: int,
    payload: OrgObCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reality = db.query(Reality).filter_by(id=reality_id, user_id=current_user.id).first()
    if not reality:
        raise HTTPException(status_code=404, detail="Reality not found")

    # Validate parent belongs to the same reality
    if payload.parent_id is not None:
        parent = (
            db.query(OrgOb)
            .filter_by(id=payload.parent_id, reality_id=reality_id)
            .first()
        )
        if not parent:
            raise HTTPException(status_code=404, detail="Parent OrgOb not found")

    org_ob = OrgOb(
        reality_id=reality_id,
        user_id=current_user.id,
        parent_id=payload.parent_id,
        name=payload.name,
        description=payload.description,
        meta=payload.meta or {},
        order_index=payload.order_index,
    )
    db.add(org_ob)
    db.commit()
    db.refresh(org_ob)
    return {"message": "OrgOb created", "org_ob": org_ob.to_dict(include_children=True)}
