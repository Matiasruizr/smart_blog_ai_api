from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import CurrentUser
from app.schemas.profile import LinkedInStatusResponse, ProfileResponse, ProfileUpdate
from app.services import profile_service

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
async def get_profile() -> ProfileResponse:
    profile = await profile_service.get()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return ProfileResponse.model_validate(profile)


@router.put("", response_model=ProfileResponse)
async def update_profile(body: ProfileUpdate, _: CurrentUser) -> ProfileResponse:
    profile = await profile_service.upsert(body)
    return ProfileResponse.model_validate(profile)


@router.get("/linkedin-status", response_model=LinkedInStatusResponse)
async def linkedin_status(_: CurrentUser) -> LinkedInStatusResponse:
    profile = await profile_service.get()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile_service.get_linkedin_status(profile)
