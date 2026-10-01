"""
SQLAlchemy engine, session, and Base for all models.
No FastAPI imports in this file.
"""
import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from backend.config import settings


def _resolve_db_url(url: str) -> str:
    """
    For SQLite file-based URLs, rewrite the path to be absolute so that
    the DB is always found regardless of the working directory.
    """
    if url.startswith("sqlite:///") and not url.startswith("sqlite:////") and url != "sqlite:///:memory:":
        relative = url[len("sqlite:///"):]
        absolute = os.path.abspath(relative)
        return f"sqlite:///{absolute}"
    return url


_db_url = _resolve_db_url(settings.DATABASE_URL)

connect_args = {"check_same_thread": False} if _db_url.startswith("sqlite") else {}

engine = create_engine(_db_url, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """Yield a DB session and close it when done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Safe to call multiple times."""
    # Import all models so their metadata is registered before create_all.
    import backend.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
