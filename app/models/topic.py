from datetime import datetime, timezone
from typing import Literal

from beanie import Document, Replace, SaveChanges, before_event
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel


class TrendingTopic(Document):
    subject: str
    brief: str
    tags: list[str] = Field(default_factory=list)
    source: Literal["hackernews", "github"]
    status: Literal["pending", "approved", "rejected"] = "pending"
    auto_publish: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @before_event([Replace, SaveChanges])
    def update_timestamp(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

    class Settings:
        name = "trending_topics"
        indexes = [
            IndexModel([("status", ASCENDING), ("created_at", DESCENDING)]),
        ]
