import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.core.auth import create_access_token
from app.main import app

SECRET = "test-secret-at-least-32-chars-long-yes"

CLAUDE_JSON = {
    "title": "Why MCP Changes AI",
    "excerpt": "A short summary of the post.",
    "content": "# Why MCP Changes AI\n\nFull post body.",
    "cover_image_search_term": "artificial intelligence",
}


def override_settings():
    return Settings(
        secret_key=SECRET,
        mongodb_uri="mongodb://localhost:27017",
        mongodb_db_name="test_smart_blog_ai",
        anthropic_api_key="test-key",
    )


app.dependency_overrides[get_settings] = override_settings


def auth_headers() -> dict:
    token = create_access_token("owner", SECRET, expire_minutes=30)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client(db):
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


def test_list_trending_empty(client):
    resp = client.get("/api/v1/automation/trending", headers=auth_headers())
    assert resp.status_code == 200
    assert resp.json() == []


def test_trending_requires_auth(client):
    resp = client.get("/api/v1/automation/trending")
    assert resp.status_code == 401


def test_scheduler_status(client):
    resp = client.get("/api/v1/automation/status", headers=auth_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert "enabled" in data
    assert "interval_hours" in data
    assert data["next_run_at"] is None


def test_run_now_returns_501(client):
    resp = client.post("/api/v1/automation/run-now", headers=auth_headers())
    assert resp.status_code == 501


def test_generate_post(client):
    with (
        patch(
            "app.routers.automation.ai_service.generate_post_content",
            new=AsyncMock(return_value=CLAUDE_JSON),
        ),
        patch(
            "app.routers.automation.ai_service.fetch_cover_image",
            new=AsyncMock(return_value="https://images.unsplash.com/photo-abc"),
        ),
    ):
        resp = client.post(
            "/api/v1/automation/generate",
            json={
                "subject": "Why MCP is changing AI",
                "brief": "Cover the protocol and adoption.",
                "tags": ["AI", "MCP"],
                "auto_publish": False,
            },
            headers=auth_headers(),
        )

    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Why MCP Changes AI"
    assert data["status"] == "draft"
    assert data["cover_image_url"] == "https://images.unsplash.com/photo-abc"
    assert data["tags"] == ["AI", "MCP"]


def test_generate_post_auto_publish(client):
    with (
        patch(
            "app.routers.automation.ai_service.generate_post_content",
            new=AsyncMock(return_value={**CLAUDE_JSON, "title": "Auto Published Post"}),
        ),
        patch(
            "app.routers.automation.ai_service.fetch_cover_image",
            new=AsyncMock(return_value=None),
        ),
    ):
        resp = client.post(
            "/api/v1/automation/generate",
            json={
                "subject": "Auto publish test",
                "brief": "Brief.",
                "tags": [],
                "auto_publish": True,
            },
            headers=auth_headers(),
        )

    assert resp.status_code == 201
    assert resp.json()["status"] == "published"
