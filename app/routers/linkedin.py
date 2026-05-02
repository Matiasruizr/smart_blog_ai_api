from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from app.config import SettingsDep
from app.core.dependencies import CurrentUser
from app.schemas.profile import ProfileResponse, ShareResponse, TokenStatusResponse
from app.services import linkedin_service, post_service, profile_service

router = APIRouter(prefix="/linkedin", tags=["linkedin"])


@router.get("/auth")
async def linkedin_auth(_: CurrentUser, settings: SettingsDep) -> RedirectResponse:
    url = linkedin_service.get_auth_url(settings)
    return RedirectResponse(url=url)


@router.get("/callback")
async def linkedin_callback(
    settings: SettingsDep,
    code: str | None = Query(default=None),
    error: str | None = Query(default=None),
) -> RedirectResponse:
    if error or not code:
        return RedirectResponse(url=f"{settings.frontend_url}?linkedin=error")
    credentials = await linkedin_service.exchange_code(code, settings)
    await profile_service.upsert_credentials(credentials)
    return RedirectResponse(url=f"{settings.frontend_url}?linkedin=connected")


@router.post("/sync", response_model=ProfileResponse)
async def sync_profile(_: CurrentUser, settings: SettingsDep) -> ProfileResponse:
    profile = await profile_service.get()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    if not profile.linkedin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="LinkedIn not connected")
    profile = await linkedin_service.sync_profile(profile, settings)
    return ProfileResponse.model_validate(profile)


@router.post("/share/{post_id}", response_model=ShareResponse)
async def share_post(post_id: str, _: CurrentUser, settings: SettingsDep) -> ShareResponse:
    post = await post_service.get_by_id(post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    profile = await profile_service.get()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    if not profile.linkedin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="LinkedIn not connected")
    url = await linkedin_service.share_post(post, profile, settings)
    post.linkedin_post_url = url
    await post.replace()
    return ShareResponse(linkedin_post_url=url)


@router.get("/token-status", response_model=TokenStatusResponse)
async def token_status(_: CurrentUser) -> TokenStatusResponse:
    profile = await profile_service.get()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return linkedin_service.get_token_status(profile)
