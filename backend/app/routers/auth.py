from datetime import datetime, timedelta
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from jose import jwt, JWTError

from sqlalchemy.orm import Session

from app.models import User
from app.db import get_db  # you will create this (example below)

router = APIRouter()

# ----------------------------
# JWT settings
# ----------------------------
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", os.getenv("SECRET_KEY", "change-me"))
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRES_MINUTES = int(os.getenv("JWT_EXPIRES_MINUTES", "60"))

bearer = HTTPBearer(auto_error=False)


def create_access_token(user_id: int) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=JWT_EXPIRES_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_optional_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if creds is None or creds.scheme.lower() != "bearer":
        return None
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        sub = payload.get("sub")
        if not sub:
            return None
        return db.get(User, int(sub))
    except (JWTError, ValueError):
        return None


GUEST_USER_EMAIL = "guest@frames.internal"


def get_guest_user(db: Session) -> User:
    """Return the shared guest account, creating it on first call."""
    import secrets as _secrets
    guest = db.query(User).filter(User.email == GUEST_USER_EMAIL).first()
    if not guest:
        guest = User(email=GUEST_USER_EMAIL, username="guest")
        guest.set_password(_secrets.token_hex(32))
        db.add(guest)
        db.commit()
        db.refresh(guest)
    return guest


PASSWORD_RESET_EXPIRES_MINUTES = 15


def create_reset_token(user_id: int) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": str(user_id),
        "type": "password_reset",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=PASSWORD_RESET_EXPIRES_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing token",
        )

    token = creds.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
            )
        user_id = int(sub)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# ----------------------------
# Schemas
# ----------------------------
class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UpdateMeRequest(BaseModel):
    username: Optional[str] = Field(default=None, min_length=2, max_length=50)
    password: Optional[str] = Field(default=None, min_length=6, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=6, max_length=128)


class UserResponse(BaseModel):
    # Keep it flexible because your `to_dict()` defines the real shape.
    # You can tighten this later.
    user: dict


class AuthResponse(BaseModel):
    message: str
    user: dict
    access_token: str


# ----------------------------
# Routes
# ----------------------------
@router.post("/register", response_model=AuthResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    # Email unique
    existing_email = db.query(User).filter(User.email == payload.email).first()
    if existing_email:
        raise HTTPException(status_code=409, detail="Email already registered")

    # Username unique
    existing_username = db.query(User).filter(User.username == payload.username).first()
    if existing_username:
        raise HTTPException(status_code=409, detail="Username already taken")

    user = User(email=payload.email, username=payload.username)
    user.set_password(payload.password)

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)

    return {
        "message": "User registered successfully",
        "user": user.to_dict(),
        "access_token": token,
    }


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not user.check_password(payload.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user.id)

    return {
        "message": "Login successful",
        "user": user.to_dict(),
        "access_token": token,
    }


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return {"user": current_user.to_dict()}


@router.put("/me", response_model=UserResponse)
def update_me(
    payload: UpdateMeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.username is not None:
        existing = db.query(User).filter(User.username == payload.username).first()
        if existing and existing.id != current_user.id:
            raise HTTPException(status_code=409, detail="Username already taken")
        current_user.username = payload.username

    if payload.password is not None:
        current_user.set_password(payload.password)

    db.commit()
    db.refresh(current_user)

    return {"user": current_user.to_dict()}


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        # Return same response to prevent email enumeration
        return {"message": "If that email is registered, a reset token has been generated."}

    token = create_reset_token(user.id)
    # NOTE: In production, email this token to the user instead of returning it.
    return {
        "message": "Reset token generated. Check your email.",
        "reset_token": token,
    }


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        data = jwt.decode(payload.token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    if data.get("type") != "password_reset":
        raise HTTPException(status_code=400, detail="Invalid reset token")

    user = db.get(User, int(data["sub"]))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.set_password(payload.new_password)
    db.commit()

    return {"message": "Password reset successfully"}
