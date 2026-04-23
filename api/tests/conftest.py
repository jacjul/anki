import pytest
import sys
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Ensure tests can import the top-level `api` package regardless of cwd.
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Force the app/database module to use SQLite during test imports.
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from api.db.database import Base, get_db
from api.main import app
from api.models.deck import Deck

@pytest.fixture(scope="session")
def engine():
    DATABASE_URL = "sqlite+pysqlite:///:memory:"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    return engine

@pytest.fixture
def db_session(engine):
    TestingSession = sessionmaker(bind=engine, autoflush= False, autocommit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def create_deck(db_session):
    deck = Deck(name ="test deck")
    db_session.add(deck)
    db_session.commit()
    db_session.refresh(deck)
    return deck.id