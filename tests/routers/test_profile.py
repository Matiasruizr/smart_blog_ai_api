import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.core.auth import create_access_token
from app.main import app

SECRET = "test-secret-at-least-32-chars-long-yes"


def override_settings():
    return Settings(
        secret_key=SECRET,
        mongodb_uri="mongodb://localhost:27017",
        mongodb_db_name="test_smart_blog_ai",
    )


app.dependency_overrides[get_settings] = override_settings


def auth_headers() -> dict:
    token = create_access_token("owner", SECRET, expire_minutes=30)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client(db):
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


def test_get_profile_returns_404_when_missing(client):
    resp = client.get("/api/v1/profile")
    assert resp.status_code == 404


def test_put_profile_requires_auth(client):
    resp = client.put("/api/v1/profile", json={
        "name": "Matias", "headline": "Engineer", "bio": "Bio.",
    })
    assert resp.status_code == 401


def test_put_profile_creates_and_returns_profile(client):
    payload = {
        "name": "Matias Ruiz",
        "headline": "Software Engineer",
        "bio": "Building things with Python.",
        "skills": ["Python", "FastAPI"],
        "links": {"github": "https://github.com/matiasruiz"},
    }
    resp = client.put("/api/v1/profile", json=payload, headers=auth_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Matias Ruiz"
    assert data["skills"] == ["Python", "FastAPI"]
    assert "id" in data
    assert "created_at" in data

    # GET /profile now returns it
    resp = client.get("/api/v1/profile")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Matias Ruiz"


def test_put_profile_is_idempotent(client):
    payload = {"name": "First", "headline": "H", "bio": "B."}
    client.put("/api/v1/profile", json=payload, headers=auth_headers())

    payload["name"] = "Updated"
    resp = client.put("/api/v1/profile", json=payload, headers=auth_headers())
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated"

    resp = client.get("/api/v1/profile")
    assert resp.json()["name"] == "Updated"


def test_linkedin_status_not_connected(client):
    client.put(
        "/api/v1/profile",
        json={"name": "Matias", "headline": "H", "bio": "B."},
        headers=auth_headers(),
    )
    resp = client.get("/api/v1/profile/linkedin-status", headers=auth_headers())
    assert resp.status_code == 200
    assert resp.json()["connected"] is False
    assert resp.json()["linkedin_id"] is None
