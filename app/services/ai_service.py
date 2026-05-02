import json

import anthropic
import httpx
from fastapi import HTTPException, status

from app.config import Settings

_UNSPLASH_URL = "https://api.unsplash.com/photos/random"
_PEXELS_URL = "https://api.pexels.com/v1/search"

_SYSTEM_PROMPT = (
    "You are a technical blogger. Given a subject and brief, generate a complete blog post. "
    "Return ONLY valid JSON with exactly these fields:\n"
    "- title: engaging post title\n"
    "- excerpt: 2-3 sentence summary for listing pages\n"
    "- content: full post body in Markdown (use headers, code blocks where appropriate)\n"
    "- cover_image_search_term: 1-3 keywords for finding a relevant stock photo"
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
    raw = message.content[0].text
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, IndexError, AttributeError):
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
