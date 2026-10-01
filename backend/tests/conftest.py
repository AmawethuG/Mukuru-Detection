"""
Pytest fixtures for backend tests.

Sets DATABASE_URL to in-memory SQLite BEFORE any app modules are imported.
The os.environ override must happen before backend.config is evaluated.
"""
import os

# --- MUST be first, before any backend import ---
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import backend.database as _db_module  # noqa: E402
from backend.database import Base  # noqa: E402
from backend.main import app  # noqa: E402


# Use StaticPool so all connections share the SAME in-memory database.
# Without StaticPool, each new connection to sqlite:///:memory: is a
# fresh empty database, which causes "no such table" errors.
_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)

# Monkey-patch the module so every import of backend.database gets
# the test engine.
_db_module.engine = _test_engine
_db_module.SessionLocal = _TestSessionLocal


def _override_get_db():
    db = _TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[_db_module.get_db] = _override_get_db


@pytest.fixture(autouse=True)
def reset_db():
    """Create all tables before each test and drop them after."""
    import backend.models  # noqa: F401 — ensure all models are registered
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture
def db_session(reset_db):
    """Yield a DB session using the test engine."""
    db = _TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(reset_db):
    """Yield a synchronous TestClient connected to the test app."""
    with TestClient(app) as c:
        yield c
