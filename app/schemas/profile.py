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
