from datetime import datetime, timezone
from typing import Optional

from beanie import Document, Replace, SaveChanges, before_event
from pydantic import BaseModel, Field


class LinkedInCredentials(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    linkedin_id: str
    last_synced_at: Optional[datetime] = None


class Profile(Document):
    name: str
    headline: str
    bio: str
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    links: dict[str, str] = Field(default_factory=dict)
    linkedin: Optional[LinkedInCredentials] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @before_event([Replace, SaveChanges])
    def update_timestamp(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

    class Settings:
        name = "profile"
