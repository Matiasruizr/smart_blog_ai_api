import json
import logging

import httpx
from bs4 import BeautifulSoup

from app.config import Settings
from app.models.topic import TrendingTopic

logger = logging.getLogger(__name__)

_HN_URL = "https://hn.algolia.com/api/v1/search"
_GITHUB_TRENDING_URL = "https://github.com/trending"

_RANKING_SYSTEM = (
    "You are a content strategist. Given a list of trending tech items, select 3-5 that "
    "would make the most compelling technical blog posts for a developer audience. "
    "Return ONLY a JSON array where each object has exactly: "
    "subject (blog post title/angle as a string), "
    "brief (2-3 sentence writing brief as a string), "
    "source (either 'hackernews' or 'github' as a string)."
)


async def scrape_hackernews(limit: int = 30) -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            _HN_URL,
            params={"tags": "story", "hitsPerPage": limit},
            timeout=10,
        )
        resp.raise_for_status()
    hits = resp.json().get("hits", [])
    return [
        {
            "title": h.get("title", ""),
            "url": h.get("url", ""),
            "points": h.get("points", 0),
            "num_comments": h.get("num_comments", 0),
            "source": "hackernews",
        }
        for h in hits
        if h.get("title")
    ]


async def scrape_github_trending() -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            _GITHUB_TRENDING_URL,
            headers={"Accept": "text/html"},
            timeout=10,
            follow_redirects=True,
        )
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    repos = []
    for article in soup.select("article.Box-row"):
        name_tag = article.select_one("h2 a")
        desc_tag = article.select_one("p")
        lang_tag = article.select_one("[itemprop='programmingLanguage']")

        if not name_tag:
            continue

        name = name_tag.get_text(strip=True).replace("\n", "").replace(" ", "")
        repos.append(
            {
                "name": name,
                "description": desc_tag.get_text(strip=True) if desc_tag else "",
                "url": f"https://github.com{name_tag.get('href', '')}",
                "language": lang_tag.get_text(strip=True) if lang_tag else "",
                "source": "github",
            }
        )
    return repos


async def rank_and_save(items: list[dict], settings: Settings) -> list[TrendingTopic]:
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    message = await client.messages.create(
        model=settings.ai_model,
        max_tokens=1024,
        system=_RANKING_SYSTEM,
        messages=[
            {"role": "user", "content": json.dumps(items, ensure_ascii=False)},
        ],
    )

    raw = message.content[0].text
    ranked: list[dict] = json.loads(raw)

    topics: list[TrendingTopic] = []
    for item in ranked[:5]:
        topic = TrendingTopic(
            subject=item["subject"],
            brief=item["brief"],
            source=item["source"],
        )
        await topic.insert()
        topics.append(topic)

    return topics


async def run_trending_cycle(settings: Settings) -> list[TrendingTopic]:
    items: list[dict] = []

    try:
        hn_items = await scrape_hackernews()
        items.extend(hn_items)
    except Exception as exc:
        logger.warning("HN scrape failed: %s", exc)

    try:
        gh_items = await scrape_github_trending()
        items.extend(gh_items)
    except Exception as exc:
        logger.warning("GitHub trending scrape failed: %s", exc)

    if not items:
        raise RuntimeError("Both trending sources failed — no items to rank")

    return await rank_and_save(items, settings)
