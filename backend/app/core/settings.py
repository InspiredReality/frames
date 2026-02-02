import os
from pathlib import Path
from pydantic import BaseModel

# Absolute path so SQLite resolves correctly regardless of CWD
_DEFAULT_DB = "sqlite:///" + str(Path(__file__).resolve().parent.parent.parent / "frames.db")

class Settings(BaseModel):
    DATABASE_URL: str = os.getenv("DATABASE_URL", _DEFAULT_DB)
    ENV: str = os.getenv("ENV", os.getenv("FLASK_ENV", "development"))

    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "uploads")

    # "*" or comma-separated list
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", os.getenv("SECRET_KEY", "change-me"))
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRES_MINUTES: int = int(os.getenv("JWT_EXPIRES_MINUTES", "60"))

settings = Settings()
