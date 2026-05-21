"""Tags router — user-scoped labels reusable across reality nodes."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.models.tag import Tag
from app.routers.auth import get_current_user

router = APIRouter()


class TagCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    color: Optional[str] = "#6366f1"


class TagUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=50)
    color: Optional[str] = None


@router.get("", status_code=200)
def list_tags(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tags = (
        db.query(Tag)
        .filter(Tag.user_id == current_user.id)
        .order_by(Tag.name)
        .all()
    )
    return {"tags": [t.to_dict() for t in tags]}


@router.post("", status_code=201)
def create_tag(
    payload: TagCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(Tag).filter_by(user_id=current_user.id, name=payload.name).first()
    if existing:
        return {"tag": existing.to_dict()}
    tag = Tag(user_id=current_user.id, name=payload.name, color=payload.color or "#6366f1")
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return {"tag": tag.to_dict()}


@router.put("/{tag_id}", status_code=200)
def update_tag(
    tag_id: int,
    payload: TagUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tag = db.query(Tag).filter_by(id=tag_id, user_id=current_user.id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    if payload.name is not None:
        tag.name = payload.name
    if payload.color is not None:
        tag.color = payload.color
    db.commit()
    db.refresh(tag)
    return {"tag": tag.to_dict()}


@router.delete("/{tag_id}", status_code=200)
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tag = db.query(Tag).filter_by(id=tag_id, user_id=current_user.id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    db.delete(tag)
    db.commit()
    return {"message": "Tag deleted"}
