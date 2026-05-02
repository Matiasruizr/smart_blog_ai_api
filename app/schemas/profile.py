from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProfileBase(BaseModel):
    name: str
    headline: str
    bio: str
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    links: dict[str, str] = Field(default_factory=dict)


class ProfileUpdate(ProfileBase):
    pass


class ProfileResponse(ProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


class LinkedInStatusResponse(BaseModel):
    connected: bool
    linkedin_id: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None


class TokenStatusResponse(BaseModel):
    valid: bool
    expires_at: Optional[datetime] = None
    expires_in_days: Optional[int] = None


class ShareResponse(BaseModel):
    linkedin_post_url: str
