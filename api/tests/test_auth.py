from api.core.settings import settings


def test_register_duplicate_username_or_email_returns_409(client):
    payload = {
        "name": "Alice",
        "lastname": "Tester",
        "username": "alice",
        "email": "alice@example.com",
        "password": "StrongPass123!",
    }

    first = client.post("/api/auth/register", json=payload)
    second = client.post("/api/auth/register", json=payload)

    assert first.status_code == 200
    assert second.status_code == 409


def test_login_and_me_returns_safe_profile(client, register_and_login):
    user_ctx = register_and_login("profile")

    me = client.get("/api/auth/me", headers=user_ctx["auth_headers"])

    assert me.status_code == 200
    body = me.json()
    assert body["username"] == user_ctx["username"]
    assert "hashed_password" not in body


def test_refresh_requires_origin_and_csrf(client, register_and_login, csrf_headers):
    register_and_login("csrf")

    missing_origin = client.post("/api/auth/refresh")
    assert missing_origin.status_code == 403

    missing_csrf = client.post(
        "/api/auth/refresh",
        headers={"origin": "http://localhost:5173"},
    )
    assert missing_csrf.status_code == 403

    success = client.post("/api/auth/refresh", headers=csrf_headers())
    assert success.status_code == 200
    assert "access_token" in success.json()


def test_logout_revokes_access_session(client, register_and_login, csrf_headers):
    user_ctx = register_and_login("logout")

    logout = client.post("/api/auth/logout", headers=csrf_headers())
    assert logout.status_code == 200

    me_after_logout = client.get("/api/auth/me", headers=user_ctx["auth_headers"])
    assert me_after_logout.status_code == 401
    assert me_after_logout.json()["detail"] == "Session revoked"


def test_login_rate_limit_returns_429(client):
    payload = {
        "name": "Rate",
        "lastname": "Limit",
        "username": "rate_user",
        "email": "rate_user@example.com",
        "password": "CorrectPassword123!",
    }
    register = client.post("/api/auth/register", json=payload)
    assert register.status_code == 200

    for _ in range(settings.LOGIN_RATE_LIMIT_ATTEMPTS):
        attempt = client.post(
            "/api/auth/login",
            data={"username": payload["username"], "password": "wrong-password"},
        )
        assert attempt.status_code == 401

    blocked = client.post(
        "/api/auth/login",
        data={"username": payload["username"], "password": "wrong-password"},
    )
    assert blocked.status_code == 429
