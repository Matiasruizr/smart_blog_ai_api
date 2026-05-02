import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import Settings
from app.services.ai_service import fetch_cover_image, generate_post_content

SETTINGS = Settings(
    secret_key="test-secret-at-least-32-chars-long-yes",
    mongodb_uri="mongodb://localhost:27017",
    mongodb_db_name="test_db",
)

CLAUDE_JSON = {
    "title": "Why MCP Changes AI",
    "excerpt": "A short summary.",
    "content": "# Why MCP Changes AI\n\nFull post body here.",
    "cover_image_search_term": "artificial intelligence",
}


async def test_generate_post_content_returns_dict():
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=json.dumps(CLAUDE_JSON))]

    with patch("app.services.ai_service.anthropic.AsyncAnthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create = AsyncMock(return_value=mock_message)
        result = await generate_post_content("Why MCP", "Cover the protocol.", SETTINGS)

    assert result["title"] == "Why MCP Changes AI"
    assert result["excerpt"] == "A short summary."
    assert "content" in result
    assert "cover_image_search_term" in result


async def test_generate_post_content_raises_on_invalid_json():
    from fastapi import HTTPException

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="not valid json")]

    with patch("app.services.ai_service.anthropic.AsyncAnthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create = AsyncMock(return_value=mock_message)
        with pytest.raises(HTTPException) as exc_info:
            await generate_post_content("Subject", "Brief", SETTINGS)
    assert exc_info.value.status_code == 502


async def test_fetch_cover_image_returns_none_when_no_keys():
    result = await fetch_cover_image("python programming", SETTINGS)
    assert result is None


async def test_fetch_cover_image_unsplash_success():
    settings = Settings(
        secret_key="test-secret-at-least-32-chars-long-yes",
        mongodb_uri="mongodb://localhost:27017",
        mongodb_db_name="test_db",
        unsplash_access_key="fake-key",
    )
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"urls": {"regular": "https://images.unsplash.com/photo-abc"}}

    with patch("app.services.ai_service.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value.__aenter__.return_value
        instance.get = AsyncMock(return_value=mock_response)
        result = await fetch_cover_image("python", settings)

    assert result == "https://images.unsplash.com/photo-abc"


async def test_fetch_cover_image_falls_back_to_pexels():
    settings = Settings(
        secret_key="test-secret-at-least-32-chars-long-yes",
        mongodb_uri="mongodb://localhost:27017",
        mongodb_db_name="test_db",
        unsplash_access_key="fake-unsplash",
        pexels_api_key="fake-pexels",
    )
    unsplash_fail = MagicMock()
    unsplash_fail.status_code = 403

    pexels_ok = MagicMock()
    pexels_ok.status_code = 200
    pexels_ok.json.return_value = {
        "photos": [{"src": {"large": "https://images.pexels.com/photo-xyz"}}]
    }

    with patch("app.services.ai_service.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value.__aenter__.return_value
        instance.get = AsyncMock(side_effect=[unsplash_fail, pexels_ok])
        result = await fetch_cover_image("python", settings)

    assert result == "https://images.pexels.com/photo-xyz"
