import logging

import anthropic
import httpx
from fastapi import HTTPException, status

from app.config import Settings

logger = logging.getLogger(__name__)

_UNSPLASH_URL = "https://api.unsplash.com/photos/random"
_PEXELS_URL = "https://api.pexels.com/v1/search"

_SYSTEM_PROMPT = (
    "You are a software engineer with 10 years of experience writing your personal tech blog. "
    "Write like a real practitioner: direct, opinionated, and grounded in real-world experience. "
    "Avoid corporate fluff, buzzword overload, and listicle filler. "
    "Use simple sentences, but don't dumb things down — assume the reader is a developer. "
    "Share genuine insight: what actually works, what to watch out for, and why it matters in practice."
)

_BLOG_POST_TOOL = {
    "name": "generate_blog_post",
    "description": (
        "Write a complete blog post on the given subject and brief. "
        "Tone: natural and conversational, like a senior engineer sharing hard-won knowledge with peers — "
        "not a textbook, not a marketing page. Language: simple but technically precise; no jargon for its own sake. "
        "Structure: short intro that hooks the reader, clear sections with practical depth, honest conclusion. "
        "The reader should finish feeling like they learned something real."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Concise, specific title — no clickbait, no 'The Ultimate Guide to'"},
            "excerpt": {"type": "string", "description": "2-3 sentences that tell the reader exactly what they'll learn and why it matters"},
            "content": {"type": "string", "description": "Full post in Markdown. Natural flow, real examples, no filler sections. Write like you're explaining to a colleague over coffee."},
            "cover_image_search_term": {"type": "string", "description": "1-3 keywords for cover image search"},
        },
        "required": ["title", "excerpt", "content", "cover_image_search_term"],
    },
}


async def generate_post_content(subject: str, brief: str, settings: Settings) -> dict:
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    message = await client.messages.create(
        model=settings.ai_model,
        max_tokens=settings.ai_max_tokens,
        system=_SYSTEM_PROMPT,
        tools=[_BLOG_POST_TOOL],
        tool_choice={"type": "tool", "name": "generate_blog_post"},
        messages=[
            {"role": "user", "content": f"Subject: {subject}\n\nBrief: {brief}"},
        ],
    )
    logger.info("Stop reason: %s | blocks: %d", message.stop_reason, len(message.content))

    for block in message.content:
        if block.type == "tool_use" and block.name == "generate_blog_post":
            return block.input

    logger.error("No tool_use block in response: %r", message.content)
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="AI returned an invalid response — no tool call found",
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
