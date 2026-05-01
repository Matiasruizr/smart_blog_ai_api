from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class GenerateRequest(BaseModel):
    subject: str
    brief: str
    tags: list[str] = Field(default_factory=list)
    auto_publish: bool = False


class TrendingTopicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    subject: str
    brief: str
    tags: list[str]
    source: Literal["hackernews", "github"]
    status: Literal["pending", "approved", "rejected"]
    created_at: datetime


class SchedulerStatusResponse(BaseModel):
    enabled: bool
    interval_hours: int
    next_run_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
