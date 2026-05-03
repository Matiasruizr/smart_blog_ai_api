import json
import logging
import re

import anthropic
import httpx
from fastapi import HTTPException, status

from app.config import Settings

logger = logging.getLogger(__name__)

_UNSPLASH_URL = "https://api.unsplash.com/photos/random"
_PEXELS_URL = "https://api.pexels.com/v1/search"

_SYSTEM_PROMPT = (
    "You are a technical blogger. Given a subject and brief, generate a complete blog post. "
    "Respond with ONLY a raw JSON object — no markdown fences, no explanation, no preamble. "
    "The JSON must have exactly these fields: "
    "title (string), excerpt (2-3 sentence summary string), "
    "content (full Markdown post body string — escape all special characters properly), "
    "cover_image_search_term (1-3 keywords string)."
)


async def generate_post_content(subject: str, brief: str, settings: Settings) -> dict:
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    message = await client.messages.create(
        model=settings.ai_model,
        max_tokens=settings.ai_max_tokens,
        system=_SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"Subject: {subject}\n\nBrief: {brief}"},
        ],
    )
    raw = message.content[0].text if message.content else ""
    logger.info("Claude raw response (first 500): %r", raw[:500])
    logger.info("Claude raw response (last 200): %r", raw[-200:])
    logger.info("Stop reason: %s", message.stop_reason)

    # Strip markdown fences if present
    fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", raw, re.DOTALL)
    if fence_match:
        raw = fence_match.group(1).strip()
        logger.info("Extracted from fence, length: %d", len(raw))
    else:
        first, last = raw.find("{"), raw.rfind("}")
        if first != -1 and last != -1:
            raw = raw[first:last + 1]
        logger.info("Used brace extraction, length: %d", len(raw))

    try:
        return json.loads(raw)
    except (json.JSONDecodeError, IndexError, AttributeError) as exc:
        logger.error("JSON parse failed: %s", exc)
        logger.error("Attempted to parse: %r", raw[:300])
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI returned an invalid response — could not parse JSON",
        )


async def fetch_cover_image(search_term: str, settings: Settings) -> str | None:
    async with httpx.AsyncClient() as client:
        if settings.unsplash_access_key:
            resp = await client.get(
                _UNSPLASH_URL,
                params={"query": search_term, "orientation": "landscape"},
                headers={"Authorization": f"Client-ID {settings.unsplash_access_key}"},
            )
            if resp.status_code == 200:
                return resp.json()["urls"]["regular"]

        if settings.pexels_api_key:
            resp = await client.get(
                _PEXELS_URL,
                params={"query": search_term, "per_page": 1},
                headers={"Authorization": settings.pexels_api_key},
            )
            if resp.status_code == 200:
                photos = resp.json().get("photos", [])
                if photos:
                    return photos[0]["src"]["large"]

    return None
