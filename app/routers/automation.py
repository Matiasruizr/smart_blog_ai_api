import re
import time

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import RedirectResponse
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


async def _create_post_from_generated(generated: dict, tags: list[str], settings: SettingsDep) -> object:
    cover_url = await ai_service.fetch_cover_image(
        generated.get("cover_image_search_term", ""), settings
    )
    slug = _slugify(generated.get("title", "post"))
    post_data = PostCreate(
        title=generated.get("title", ""),
        slug=slug,
        content=generated.get("content", ""),
        excerpt=generated.get("excerpt", ""),
        tags=tags,
        cover_image_url=cover_url,
    )
    try:
        return await post_service.create(post_data, settings.ai_model)
    except DuplicateKeyError:
        post_data.slug = f"{slug}-{int(time.time())}"
        return await post_service.create(post_data, settings.ai_model)


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
    post = await _create_post_from_generated(generated, body.tags, settings)

    if body.auto_publish:
        post = await post_service.publish(post)

    return PostResponse.model_validate(post)


@router.get("/approve/{topic_id}")
async def approve_topic(topic_id: str, settings: SettingsDep) -> RedirectResponse:
    topic = await TrendingTopic.get(topic_id)
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

    topic.status = "approved"
    await topic.replace()

    generated = await ai_service.generate_post_content(topic.subject, topic.brief, settings)
    post = await _create_post_from_generated(generated, topic.tags, settings)

    return RedirectResponse(
        url=f"{settings.frontend_url}?approved=true&post_id={post.id}",
        status_code=status.HTTP_302_FOUND,
    )


@router.get("/status", response_model=SchedulerStatusResponse)
async def scheduler_status(_: CurrentUser, settings: SettingsDep) -> SchedulerStatusResponse:
    return SchedulerStatusResponse(
        enabled=settings.scheduler_enabled,
        interval_hours=settings.automation_interval_hours,
        next_run_at=None,
        last_run_at=None,
    )


@router.post("/run-now", status_code=status.HTTP_202_ACCEPTED)
async def run_now(_: CurrentUser, settings: SettingsDep) -> dict:
    from app.services.scheduler import run_automation_cycle
    import asyncio

    asyncio.create_task(run_automation_cycle(settings))
    return {"detail": "Automation cycle triggered"}
