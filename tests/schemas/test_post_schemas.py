from datetime import datetime, timezone

from app.schemas.post import PostCreate, PostResponse, PostUpdate


def test_post_create_defaults():
    post = PostCreate(
        title="My Post",
        slug="my-post",
        content="# Hello",
        excerpt="Short summary",
    )
    assert post.tags == []
    assert post.cover_image_url is None
    assert post.meta_title is None
    assert post.meta_description is None
    assert post.auto_publish is False


def test_post_update_shares_base_fields():
    post = PostUpdate(
        title="Updated",
        slug="updated-post",
        content="# Updated content",
        excerpt="Updated summary",
        cover_image_url="https://example.com/img.jpg",
        meta_title="SEO Title",
    )
    assert post.cover_image_url == "https://example.com/img.jpg"
    assert post.meta_title == "SEO Title"


def test_post_response_from_attributes():
    class FakePost:
        id = "abc123"
        title = "My Post"
        slug = "my-post"
        content = "# Hello"
        excerpt = "Summary"
        tags = ["python"]
        cover_image_url = None
        meta_title = None
        meta_description = None
        status = "published"
        ai_model = "claude-sonnet-4-6"
        topic_id = None
        linkedin_post_url = None
        published_at = None
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)

    response = PostResponse.model_validate(FakePost())
    assert response.title == "My Post"
    assert response.id == "abc123"
    assert response.status == "published"
