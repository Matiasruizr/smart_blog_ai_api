from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.core.auth import create_access_token
from app.main import app
from app.models.profile import LinkedInCredentials

SECRET = "test-secret-at-least-32-chars-long-yes"


def override_settings():
    return Settings(
        secret_key=SECRET,
        mongodb_uri="mongodb://localhost:27017",
        mongodb_db_name="test_smart_blog_ai",
        frontend_url="http://localhost:3000",
        linkedin_client_id="test-client-id",
        linkedin_client_secret="test-secret",
    )


app.dependency_overrides[get_settings] = override_settings


def auth_headers() -> dict:
    token = create_access_token("owner", SECRET, expire_minutes=30)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client(db):
    with TestClient(app, raise_server_exceptions=True, follow_redirects=False) as c:
        yield c


def test_auth_redirects_to_linkedin(client):
    resp = client.get("/api/v1/linkedin/auth", headers=auth_headers())
    assert resp.status_code == 307
    assert "linkedin.com/oauth" in resp.headers["location"]


def test_auth_requires_auth(client):
    resp = client.get("/api/v1/linkedin/auth")
    assert resp.status_code == 401


def test_callback_with_error_redirects(client):
    resp = client.get("/api/v1/linkedin/callback?error=access_denied")
    assert resp.status_code == 307
    assert "linkedin=error" in resp.headers["location"]


def test_callback_exchanges_code_and_redirects(client):
    fake_creds = LinkedInCredentials(
        access_token="tok",
        linkedin_id="urn:li:person:123",
        token_expires_at=datetime.now(timezone.utc),
    )
    with (
        patch(
            "app.routers.linkedin.linkedin_service.exchange_code",
            new=AsyncMock(return_value=fake_creds),
        ),
        patch(
            "app.routers.linkedin.profile_service.upsert_credentials",
            new=AsyncMock(return_value=None),
        ),
    ):
        resp = client.get("/api/v1/linkedin/callback?code=abc123")
    assert resp.status_code == 307
    assert "linkedin=connected" in resp.headers["location"]


def test_token_status_no_profile(client):
    resp = client.get("/api/v1/linkedin/token-status", headers=auth_headers())
    assert resp.status_code == 404
