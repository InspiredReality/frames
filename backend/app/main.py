from pathlib import Path

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db import engine, Base, get_db

# Import models so they register with Base.metadata
from app.models import User, Wall, Picture, PictureFrame  # noqa: F401

# Routers
from app.routers.auth import router as auth_router
from app.routers.walls import router as walls_router
from app.routers.pictures import router as pictures_router
from app.routers.models3d import router as models3d_router


def create_app() -> FastAPI:
    app = FastAPI(title="Frames API")

    # Create tables (safe no-op if they already exist)
    Base.metadata.create_all(bind=engine)

    # -------------------
    # CORS
    # -------------------
    if settings.CORS_ORIGINS.strip() == "*":
        allow_origins = ["*"]
    else:
        allow_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
        expose_headers=["Content-Type", "Authorization"],
    )

    # -------------------
    # Ensure upload folders exist
    # -------------------
    upload_root = Path(settings.UPLOAD_FOLDER)
    (upload_root / "frames").mkdir(parents=True, exist_ok=True)
    (upload_root / "walls").mkdir(parents=True, exist_ok=True)
    (upload_root / "models").mkdir(parents=True, exist_ok=True)

    # -------------------
    # Routers (Blueprints -> Routers)
    # -------------------
    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
    app.include_router(walls_router, prefix="/api/walls", tags=["walls"])
    app.include_router(pictures_router, prefix="/api/pictures", tags=["pictures"])
    app.include_router(models3d_router, prefix="/api/models", tags=["models"])

    # -------------------
    # Root + health + status
    # -------------------
    @app.get("/")
    def root():
        return {"message": "Frames API", "health": "/api/health", "status": "/api/status"}

    # MUST be fast + DB-independent for Railway
    @app.get("/api/health")
    def health():
        return {"status": "healthy", "message": "Frames API is running"}

    @app.get("/api/status")
    def status(db: Session = Depends(get_db)):
        status = {
            "status": "healthy",
            "message": "Frames API is running",
            "environment": settings.ENV,
        }

        try:
            db.execute(text("SET statement_timeout = 5000"))
            db.execute(text("SELECT 1"))
            status["database"] = "connected"
        except Exception as e:
            status["database"] = "disconnected"
            status["database_error"] = str(e)[:200]

        return status

    @app.get("/api/debug/token")
    def debug_token(request: Request):
        auth_header = request.headers.get("Authorization", "Not provided")
        return {
            "auth_header": (auth_header[:50] + "...") if len(auth_header) > 50 else auth_header
        }

    return app


app = create_app()
