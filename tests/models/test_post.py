import asyncio
from datetime import datetime

import pytest
from pymongo.errors import DuplicateKeyError

from app.models.post import BlogPost


async def test_blogpost_defaults(db):
    post = BlogPost(
        title="Test Post",
        slug="test-post",
        content="# Hello World",
        excerpt="A short summary",
        ai_model="claude-sonnet-4-6",
    )
    await post.insert()

    assert post.status == "draft"
    assert post.tags == []
    assert post.topic_id is None
    assert post.linkedin_post_id is None
    assert post.published_at is None
    assert isinstance(post.created_at, datetime)
    assert isinstance(post.updated_at, datetime)
    assert post.id is not None


async def test_blogpost_explicit_fields(db):
    from beanie import PydanticObjectId

    topic_id = PydanticObjectId()
    post = BlogPost(
        title="My Post",
        slug="my-post",
        content="# Content",
        excerpt="Summary",
        tags=["python", "ai"],
        status="published",
        topic_id=topic_id,
        linkedin_post_id="li:123",
        ai_model="claude-sonnet-4-6",
        published_at=datetime.utcnow(),
    )
    await post.insert()

    assert post.tags == ["python", "ai"]
    assert post.status == "published"
    assert post.topic_id == topic_id
    assert post.linkedin_post_id == "li:123"
    assert post.published_at is not None


async def test_updated_at_changes_on_replace(db):
    post = BlogPost(
        title="Original",
        slug="update-ts-test",
        content="# Body",
        excerpt="Summary",
        ai_model="claude-sonnet-4-6",
    )
    await post.insert()
    original_updated_at = post.updated_at

    await asyncio.sleep(0.01)
    post.title = "Changed"
    await post.replace()

    assert post.updated_at > original_updated_at


async def test_slug_must_be_unique(db):
    await BlogPost(
        title="First", slug="dupe-slug", content="c", excerpt="e", ai_model="m"
    ).insert()
    with pytest.raises(DuplicateKeyError):
        await BlogPost(
            title="Second", slug="dupe-slug", content="c", excerpt="e", ai_model="m"
        ).insert()
