from __future__ import annotations

import secrets
from pathlib import Path
from typing import Optional, Set

from fastapi import HTTPException, UploadFile, status
from PIL import Image as PILImage

DEFAULT_ALLOWED_EXTENSIONS: Set[str] = {"png", "jpg", "jpeg", "gif", "webp"}
DEFAULT_MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10MB


def _ext_from_filename(filename: str) -> str:
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[1].lower().strip()


def make_safe_filename(
    user_id: int,
    original_filename: str,
    allowed_extensions: Set[str] = DEFAULT_ALLOWED_EXTENSIONS,
) -> str:
    """
    Best practice: never trust the client filename.
    Keep only a vetted extension; generate the base name yourself.
    """
    ext = _ext_from_filename(original_filename)
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File type not allowed",
        )
    return f"{user_id}_{secrets.token_hex(8)}.{ext}"


async def save_upload_with_limit(
    upload: UploadFile,
    dest: Path,
    max_bytes: int = DEFAULT_MAX_UPLOAD_BYTES,
    chunk_size: int = 1024 * 1024,  # 1MB
) -> None:
    """
    Stream the uploaded file to disk with a hard size limit.
    Avoids reading the entire file into memory.
    """
    written = 0
    try:
        with dest.open("wb") as f:
            while True:
                chunk = await upload.read(chunk_size)
                if not chunk:
                    break
                written += len(chunk)
                if written > max_bytes:
                    # Clean up partial file
                    try:
                        dest.unlink(missing_ok=True)
                    except Exception:
                        pass
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="File too large",
                    )
                f.write(chunk)
    finally:
        try:
            await upload.close()
        except Exception:
            pass


def verify_image_file(path: Path) -> None:
    """
    Verifies the file is a valid image (structure check).
    Deletes the file and raises 400 if invalid.
    """
    try:
        with PILImage.open(path) as im:
            im.verify()
    except Exception:
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is not a valid image",
        )
