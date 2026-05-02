import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import Settings

SETTINGS = Settings(
    secret_key="test-secret-at-least-32-chars-long-yes",
    mongodb_uri="mongodb://localhost:27017",
    mongodb_db_name="test_db",
)

HN_RESPONSE = {
    "hits": [
        {"title": "Why Rust is fast", "url": "https://example.com", "points": 500, "num_comments": 120},
        {"title": "New Python 3.14 features", "url": "https://python.org", "points": 300, "num_comments": 80},
    ]
}

GITHUB_HTML = """
<html><body>
<article class="Box-row">
  <h2><a href="/user/cool-repo">user / cool-repo</a></h2>
  <p>A very cool repository</p>
</article>
</body></html>
"""


async def test_scrape_hackernews_returns_items():
    from app.services.trending_service import scrape_hackernews

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = HN_RESPONSE
    mock_resp.raise_for_status = MagicMock()

    with patch("app.services.trending_service.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value.__aenter__.return_value
        instance.get = AsyncMock(return_value=mock_resp)
        items = await scrape_hackernews(limit=2)

    assert len(items) == 2
    assert items[0]["title"] == "Why Rust is fast"
    assert items[0]["source"] == "hackernews"


async def test_scrape_github_trending_returns_items():
    from app.services.trending_service import scrape_github_trending

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = GITHUB_HTML
    mock_resp.raise_for_status = MagicMock()

    with patch("app.services.trending_service.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value.__aenter__.return_value
        instance.get = AsyncMock(return_value=mock_resp)
        items = await scrape_github_trending()

    assert len(items) == 1
    assert "cool-repo" in items[0]["name"]
    assert items[0]["source"] == "github"


async def test_run_trending_cycle_continues_on_one_failure():
    from app.services.trending_service import run_trending_cycle

    ranked_topics = [
        {"subject": "Why Rust is fast", "brief": "A brief.", "source": "hackernews"}
    ]
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=json.dumps(ranked_topics))]

    with (
        patch(
            "app.services.trending_service.scrape_hackernews",
            new=AsyncMock(side_effect=Exception("HN down")),
        ),
        patch(
            "app.services.trending_service.scrape_github_trending",
            new=AsyncMock(return_value=[{"title": "repo", "source": "github"}]),
        ),
        patch("app.services.trending_service.anthropic.AsyncAnthropic") as MockClient,
        patch("app.models.topic.TrendingTopic.insert", new=AsyncMock()),
    ):
        instance = MockClient.return_value
        instance.messages.create = AsyncMock(return_value=mock_message)
        topics = await run_trending_cycle(SETTINGS)

    assert len(topics) == 1
