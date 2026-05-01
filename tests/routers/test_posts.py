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


def test_list_posts_empty(client):
    resp = client.get("/api/v1/posts")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_post_requires_auth(client):
    resp = client.post("/api/v1/posts", json={
        "title": "T", "slug": "t", "content": "c", "excerpt": "e",
    })
    assert resp.status_code == 401


def test_create_and_get_post(client):
    resp = client.post(
        "/api/v1/posts",
        json={"title": "Hello", "slug": "hello", "content": "# Hi", "excerpt": "Short"},
        headers=auth_headers(),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["slug"] == "hello"
    assert data["status"] == "draft"

    # draft not visible on public listing
    resp = client.get("/api/v1/posts")
    assert resp.json() == []

    # publish it
    post_id = data["id"]
    resp = client.patch(f"/api/v1/posts/{post_id}/publish", headers=auth_headers())
    assert resp.status_code == 200
    assert resp.json()["status"] == "published"

    # now visible on public listing
    resp = client.get("/api/v1/posts")
    assert len(resp.json()) == 1

    # get by slug
    resp = client.get("/api/v1/posts/hello")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Hello"


def test_delete_post(client):
    resp = client.post(
        "/api/v1/posts",
        json={"title": "Del", "slug": "del-post", "content": "c", "excerpt": "e"},
        headers=auth_headers(),
    )
    post_id = resp.json()["id"]

    # publish so it's reachable by slug before deletion
    client.patch(f"/api/v1/posts/{post_id}/publish", headers=auth_headers())
    assert client.get("/api/v1/posts/del-post").status_code == 200

    resp = client.delete(f"/api/v1/posts/{post_id}", headers=auth_headers())
    assert resp.status_code == 204

    # slug endpoint now returns 404
    resp = client.get("/api/v1/posts/del-post")
    assert resp.status_code == 404


def test_duplicate_slug_returns_409(client):
    payload = {"title": "T", "slug": "same", "content": "c", "excerpt": "e"}
    client.post("/api/v1/posts", json=payload, headers=auth_headers())
    resp = client.post("/api/v1/posts", json=payload, headers=auth_headers())
    assert resp.status_code == 409
