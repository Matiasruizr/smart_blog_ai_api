import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.core.security import hash_password
from app.main import app

SECRET = "test-secret-at-least-32-chars-long-yes"
PASSWORD = "supersecret"


def override_settings():
    return Settings(
        secret_key=SECRET,
        mongodb_uri="mongodb://localhost:27017",
        mongodb_db_name="test_smart_blog_ai",
        owner_username="admin",
        owner_password_hash=hash_password(PASSWORD),
    )


app.dependency_overrides[get_settings] = override_settings


@pytest.fixture
def client(db):
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


def test_login_returns_token(client):
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": PASSWORD},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "wrongpassword"},
    )
    assert resp.status_code == 401


def test_login_wrong_username(client):
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "hacker", "password": PASSWORD},
    )
    assert resp.status_code == 401


def test_token_can_be_used_for_protected_endpoint(client):
    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": PASSWORD},
    )
    token = login_resp.json()["access_token"]

    resp = client.get(
        "/api/v1/posts/drafts",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
