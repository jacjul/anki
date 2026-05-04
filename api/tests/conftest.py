import pytest
import sys
import os
import uuid
from pathlib import Path
from sqlalchemy import create_engine, delete
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
from api.auth import helper as auth_helper

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
        session.rollback()
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(delete(table))
        session.commit()
        session.close()


@pytest.fixture(autouse=True)
def clear_login_rate_limit_state():
    auth_helper.clear_rate_limit_state_for_tests()


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
def register_and_login(client):
    def _register_and_login(prefix: str = "user", password: str = "Testpass123!") -> dict:
        suffix = uuid.uuid4().hex[:10]
        username = f"{prefix}_{suffix}"
        email = f"{username}@example.com"

        register_payload = {
            "name": "Test",
            "lastname": "User",
            "username": username,
            "email": email,
            "password": password,
        }

        register_response = client.post("/api/auth/register", json=register_payload)
        assert register_response.status_code == 200

        login_response = client.post(
            "/api/auth/login",
            data={"username": username, "password": password},
        )
        assert login_response.status_code == 200

        access_token = login_response.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {access_token}"}

        profile_response = client.get("/api/auth/me", headers=auth_headers)
        assert profile_response.status_code == 200
        user_profile = profile_response.json()

        return {
            "username": username,
            "email": email,
            "password": password,
            "access_token": access_token,
            "auth_headers": auth_headers,
            "user": user_profile,
        }

    return _register_and_login


@pytest.fixture
def csrf_headers(client):
    def _csrf_headers(origin: str = "http://localhost:5173") -> dict:
        csrf_token = client.cookies.get("csrf_token")
        return {
            "origin": origin,
            "x-csrf-token": csrf_token or "",
        }

    return _csrf_headers


@pytest.fixture
def create_deck_for_user(client):
    def _create_deck_for_user(user_ctx: dict, name: str = "deck", public: bool = False) -> dict:
        response = client.post(
            "/api/deck/create",
            json={"name": name, "public": public},
            headers=user_ctx["auth_headers"],
        )
        assert response.status_code == 200
        return response.json()

    return _create_deck_for_user