from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import sessionmaker, Session, declarative_base

from app.core.settings import settings

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

_engine_kwargs = {"future": True}
if _is_sqlite:
    # NullPool closes connections after each use, ensuring writes flush to disk
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
    _engine_kwargs["poolclass"] = NullPool
else:
    _engine_kwargs["pool_pre_ping"] = True

engine = create_engine(settings.DATABASE_URL, **_engine_kwargs)

# SQLite: enable WAL mode and foreign keys for each connection
if _is_sqlite:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
