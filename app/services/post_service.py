from datetime import datetime, timezone

from app.models.post import BlogPost
from app.schemas.post import PostCreate, PostUpdate


async def list_published(page: int, size: int) -> list[BlogPost]:
    skip = (page - 1) * size
    return (
        await BlogPost.find(
            BlogPost.status == "published",
            BlogPost.is_deleted == False,
        )
        .sort(-BlogPost.created_at)
        .skip(skip)
        .limit(size)
        .to_list()
    )


async def list_drafts(page: int, size: int) -> list[BlogPost]:
    skip = (page - 1) * size
    return (
        await BlogPost.find(
            BlogPost.status == "draft",
            BlogPost.is_deleted == False,
        )
        .sort(-BlogPost.created_at)
        .skip(skip)
        .limit(size)
        .to_list()
    )


async def get_by_slug(slug: str) -> BlogPost | None:
    return await BlogPost.find_one(
        BlogPost.slug == slug,
        BlogPost.status == "published",
        BlogPost.is_deleted == False,
    )


async def get_by_id(post_id: str) -> BlogPost | None:
    return await BlogPost.find_one(
        BlogPost.id == post_id,
        BlogPost.is_deleted == False,
    )


async def create(data: PostCreate, ai_model: str) -> BlogPost:
    post = BlogPost(
        title=data.title,
        slug=data.slug,
        content=data.content,
        excerpt=data.excerpt,
        tags=data.tags,
        cover_image_url=data.cover_image_url,
        meta_title=data.meta_title,
        meta_description=data.meta_description,
        ai_model=ai_model,
    )
    await post.insert()
    return post


async def update(post: BlogPost, data: PostUpdate) -> BlogPost:
    post.title = data.title
    post.slug = data.slug
    post.content = data.content
    post.excerpt = data.excerpt
    post.tags = data.tags
    post.cover_image_url = data.cover_image_url
    post.meta_title = data.meta_title
    post.meta_description = data.meta_description
    await post.replace()
    return post


async def publish(post: BlogPost) -> BlogPost:
    post.status = "published"
    post.published_at = datetime.now(timezone.utc)
    await post.replace()
    return post


async def unpublish(post: BlogPost) -> BlogPost:
    post.status = "draft"
    post.published_at = None
    await post.replace()
    return post


async def soft_delete(post: BlogPost) -> None:
    post.is_deleted = True
    await post.replace()
