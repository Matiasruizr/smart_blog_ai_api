import asyncio
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models.topic import TrendingTopic


async def test_topic_defaults(db):
    topic = TrendingTopic(
        subject="Why MCP is changing AI integrations",
        brief="Cover the protocol, real use cases, and adoption curve.",
        source="hackernews",
    )
    await topic.insert()

    assert topic.tags == []
    assert topic.status == "pending"
    assert topic.auto_publish is False
    assert isinstance(topic.created_at, datetime)
    assert isinstance(topic.updated_at, datetime)
    assert topic.id is not None


async def test_topic_explicit_fields(db):
    topic = TrendingTopic(
        subject="Top GitHub repos this week",
        brief="Summarise the top 5 trending repos.",
        tags=["open-source", "github"],
        source="github",
        status="approved",
        auto_publish=True,
    )
    await topic.insert()

    assert topic.tags == ["open-source", "github"]
    assert topic.source == "github"
    assert topic.status == "approved"
    assert topic.auto_publish is True


def test_topic_invalid_source_rejected():
    with pytest.raises(ValidationError):
        TrendingTopic(
            subject="Bad source",
            brief="Brief.",
            source="reddit",
        )


async def test_updated_at_changes_on_replace(db):
    topic = TrendingTopic(
        subject="Original subject",
        brief="Brief.",
        source="hackernews",
    )
    await topic.insert()
    original_updated_at = topic.updated_at

    await asyncio.sleep(0.01)
    topic.status = "approved"
    await topic.replace()

    assert topic.updated_at > original_updated_at
