from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PostBase(BaseModel):
    title: str
    slug: str
    content: str
    excerpt: str
    tags: list[str] = Field(default_factory=list)
    cover_image_url: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


class PostCreate(PostBase):
    auto_publish: bool = False


class PostUpdate(PostBase):
    pass


class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: Literal["draft", "published"]
    ai_model: str
    topic_id: Optional[str] = None
    linkedin_post_url: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    @field_validator("id", mode="before")
    @classmethod
    def _coerce_id(cls, value: object) -> str:
        return str(value)

    @field_validator("topic_id", mode="before")
    @classmethod
    def _coerce_topic_id(cls, value: object) -> Optional[str]:
        if value is None:
            return None
        return str(value)
