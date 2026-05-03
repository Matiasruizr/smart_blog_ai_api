from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.core.auth import create_access_token
from app.main import app

SECRET = "test-secret-at-least-32-chars-long-yes"

CLAUDE_JSON = {
    "title": "Generated Post Title",
    "excerpt": "Short excerpt here.",
    "content": "# Generated Post\n\nBody text.",
    "cover_image_search_term": "technology",
}


def override_settings():
    return Settings(
        secret_key=SECRET,
        mongodb_uri="mongodb://localhost:27017",
        mongodb_db_name="test_smart_blog_ai",
        anthropic_api_key="test-key",
        email_from="test@example.com",
        email_to_owner="owner@example.com",
    )


app.dependency_overrides[get_settings] = override_settings


def auth_headers() -> dict:
    token = create_access_token("owner", SECRET, expire_minutes=30)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client(db):
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


def test_brief_submitted_requires_auth(client):
    resp = client.post("/api/v1/webhooks/brief-submitted", json={"topic_id": "abc"})
    assert resp.status_code == 401


def test_brief_submitted_topic_not_found(client):
    resp = client.post(
        "/api/v1/webhooks/brief-submitted",
        json={"topic_id": "000000000000000000000000"},
        headers=auth_headers(),
    )
    assert resp.status_code == 404


def test_brief_submitted_generates_post(client, db):
    from app.models.topic import TrendingTopic
    import asyncio

    async def insert_topic():
        topic = TrendingTopic(
            subject="Test subject",
            brief="Test brief.",
            source="hackernews",
        )
        await topic.insert()
        return str(topic.id)

    topic_id = asyncio.get_event_loop().run_until_complete(insert_topic())

    with (
        patch(
            "app.routers.webhooks.ai_service.generate_post_content",
            new=AsyncMock(return_value=CLAUDE_JSON),
        ),
        patch(
            "app.routers.webhooks.ai_service.fetch_cover_image",
            new=AsyncMock(return_value=None),
        ),
    ):
        resp = client.post(
            "/api/v1/webhooks/brief-submitted",
            json={"topic_id": topic_id},
            headers=auth_headers(),
        )

    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Generated Post Title"
    assert data["status"] == "draft"


def test_post_published_not_found(client):
    resp = client.post(
        "/api/v1/webhooks/post-published",
        json={"post_id": "000000000000000000000000"},
        headers=auth_headers(),
    )
    assert resp.status_code == 404


def test_publish_post_fires_background_email(client):
    from app.models.post import BlogPost
    import asyncio

    async def insert_post():
        post = BlogPost(
            title="Email Test",
            slug="email-test-bg",
            content="# Test",
            excerpt="Test excerpt",
            ai_model="claude-sonnet-4-6",
        )
        await post.insert()
        return str(post.id)

    post_id = asyncio.get_event_loop().run_until_complete(insert_post())

    with patch("app.routers.post.email_service.send_post_published") as mock_email:
        resp = client.patch(
            f"/api/v1/posts/{post_id}/publish",
            headers=auth_headers(),
        )

    assert resp.status_code == 200
    assert resp.json()["status"] == "published"
    mock_email.assert_called_once()
