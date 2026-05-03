import re
import time

from fastapi import APIRouter, HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.config import SettingsDep
from app.core.dependencies import CurrentUser
from app.models.topic import TrendingTopic
from app.schemas.automation import BriefSubmittedRequest, PostPublishedRequest
from app.schemas.post import PostCreate, PostResponse
from app.services import ai_service, email_service, post_service

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


@router.post("/brief-submitted", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def brief_submitted(
    body: BriefSubmittedRequest,
    _: CurrentUser,
    settings: SettingsDep,
) -> PostResponse:
    topic = await TrendingTopic.get(body.topic_id)
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

    topic.status = "approved"
    await topic.replace()

    generated = await ai_service.generate_post_content(topic.subject, topic.brief, settings)
    cover_url = await ai_service.fetch_cover_image(
        generated.get("cover_image_search_term", topic.subject), settings
    )

    slug = _slugify(generated.get("title", topic.subject))
    post_data = PostCreate(
        title=generated.get("title", topic.subject),
        slug=slug,
        content=generated.get("content", ""),
        excerpt=generated.get("excerpt", ""),
        tags=topic.tags,
        cover_image_url=cover_url,
    )

    try:
        post = await post_service.create(post_data, settings.ai_model)
    except DuplicateKeyError:
        post_data.slug = f"{slug}-{int(time.time())}"
        post = await post_service.create(post_data, settings.ai_model)

    return PostResponse.model_validate(post)


@router.post("/post-published")
async def post_published(
    body: PostPublishedRequest,
    _: CurrentUser,
    settings: SettingsDep,
) -> dict:
    post = await post_service.get_by_id(body.post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    email_service.send_post_published(post, settings)
    return {"detail": "notification sent"}
