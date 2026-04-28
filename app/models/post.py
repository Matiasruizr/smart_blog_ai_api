from datetime import datetime, timezone
from typing import Literal, Optional

from beanie import Document, PydanticObjectId, Replace, SaveChanges, before_event
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel


class BlogPost(Document):
    title: str
    slug: str
    content: str
    excerpt: str
    tags: list[str] = Field(default_factory=list)
    status: Literal["draft", "published"] = "draft"
    topic_id: Optional[PydanticObjectId] = None
    linkedin_post_id: Optional[str] = None
    ai_model: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    published_at: Optional[datetime] = None

    @before_event([Replace, SaveChanges])
    def update_timestamp(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

    class Settings:
        name = "blog_posts"
        indexes = [
            IndexModel([("slug", ASCENDING)], unique=True),
            IndexModel([("status", ASCENDING), ("created_at", DESCENDING)]),
        ]
