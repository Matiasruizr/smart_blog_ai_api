from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.config import SettingsDep
from app.core.dependencies import CurrentUser
from app.schemas.post import PostCreate, PostResponse, PostUpdate
from app.services import email_service, post_service

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("", response_model=list[PostResponse])
async def list_posts(page: int = 1, size: int = 10) -> list[PostResponse]:
    posts = await post_service.list_published(page, size)
    return [PostResponse.model_validate(p) for p in posts]


@router.get("/drafts", response_model=list[PostResponse])
async def list_drafts(
    _: CurrentUser,
    page: int = 1,
    size: int = 10,
) -> list[PostResponse]:
    posts = await post_service.list_drafts(page, size)
    return [PostResponse.model_validate(p) for p in posts]


@router.get("/{slug}", response_model=PostResponse)
async def get_post(slug: str) -> PostResponse:
    post = await post_service.get_by_slug(slug)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return PostResponse.model_validate(post)


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    body: PostCreate,
    _: CurrentUser,
    settings: SettingsDep,
) -> PostResponse:
    try:
        post = await post_service.create(body, settings.ai_model)
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already exists")
    return PostResponse.model_validate(post)


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: str,
    body: PostUpdate,
    _: CurrentUser,
) -> PostResponse:
    post = await post_service.get_by_id(post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    try:
        post = await post_service.update(post, body)
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already exists")
    return PostResponse.model_validate(post)


@router.patch("/{post_id}/publish", response_model=PostResponse)
async def publish_post(
    post_id: str,
    _: CurrentUser,
    background_tasks: BackgroundTasks,
    settings: SettingsDep,
) -> PostResponse:
    post = await post_service.get_by_id(post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    post = await post_service.publish(post)
    background_tasks.add_task(email_service.send_post_published, post, settings)
    return PostResponse.model_validate(post)


@router.patch("/{post_id}/unpublish", response_model=PostResponse)
async def unpublish_post(post_id: str, _: CurrentUser) -> PostResponse:
    post = await post_service.get_by_id(post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    post = await post_service.unpublish(post)
    return PostResponse.model_validate(post)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: str, _: CurrentUser) -> None:
    post = await post_service.get_by_id(post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    await post_service.soft_delete(post)
