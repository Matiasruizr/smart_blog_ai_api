import re
import time

from fastapi import APIRouter, HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.config import SettingsDep
from app.core.dependencies import CurrentUser
from app.models.topic import TrendingTopic
from app.schemas.automation import (
    GenerateRequest,
    SchedulerStatusResponse,
    TrendingTopicResponse,
)
from app.schemas.post import PostCreate, PostResponse
from app.services import ai_service, post_service

router = APIRouter(prefix="/automation", tags=["automation"])


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


@router.get("/trending", response_model=list[TrendingTopicResponse])
async def list_trending(_: CurrentUser) -> list[TrendingTopicResponse]:
    topics = (
        await TrendingTopic.find(TrendingTopic.status == "pending")
        .sort(-TrendingTopic.created_at)
        .limit(20)
        .to_list()
    )
    return [TrendingTopicResponse.model_validate(t) for t in topics]


@router.post("/generate", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def generate_post(
    body: GenerateRequest,
    _: CurrentUser,
    settings: SettingsDep,
) -> PostResponse:
    generated = await ai_service.generate_post_content(body.subject, body.brief, settings)
    cover_url = await ai_service.fetch_cover_image(
        generated.get("cover_image_search_term", body.subject), settings
    )

    slug = _slugify(generated.get("title", body.subject))
    post_data = PostCreate(
        title=generated.get("title", body.subject),
        slug=slug,
        content=generated.get("content", ""),
        excerpt=generated.get("excerpt", ""),
        tags=body.tags,
        cover_image_url=cover_url,
        auto_publish=body.auto_publish,
    )

    try:
        post = await post_service.create(post_data, settings.ai_model)
    except DuplicateKeyError:
        post_data.slug = f"{slug}-{int(time.time())}"
        post = await post_service.create(post_data, settings.ai_model)

    if body.auto_publish:
        post = await post_service.publish(post)

    return PostResponse.model_validate(post)


@router.get("/status", response_model=SchedulerStatusResponse)
async def scheduler_status(_: CurrentUser, settings: SettingsDep) -> SchedulerStatusResponse:
    return SchedulerStatusResponse(
        enabled=settings.scheduler_enabled,
        interval_hours=settings.automation_interval_hours,
        next_run_at=None,
        last_run_at=None,
    )


@router.post("/run-now", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def run_now(_: CurrentUser) -> dict:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Scheduler not yet implemented",
    )
