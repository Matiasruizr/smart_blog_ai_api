import json
import logging
import re

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


def _extract_json_payload(raw: str) -> str:
    candidate = raw.strip()
    if not candidate:
        raise ValueError("AI ranking response was empty")

    fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", candidate, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()

    first_bracket = candidate.find("[")
    last_bracket = candidate.rfind("]")
    if first_bracket != -1 and last_bracket != -1 and first_bracket < last_bracket:
        return candidate[first_bracket : last_bracket + 1].strip()

    return candidate


def _parse_ranked_topics(raw: str) -> list[dict]:
    payload = _extract_json_payload(raw)
    parsed = json.loads(payload)

    if not isinstance(parsed, list):
        raise ValueError("AI ranking response was not a JSON array")

    validated: list[dict] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue

        subject = item.get("subject")
        brief = item.get("brief")
        source = item.get("source")
        if (
            isinstance(subject, str)
            and subject.strip()
            and isinstance(brief, str)
            and brief.strip()
            and source in {"hackernews", "github"}
        ):
            validated.append(
                {
                    "subject": subject.strip(),
                    "brief": brief.strip(),
                    "source": source,
                }
            )

    if not validated:
        raise ValueError("AI ranking response had no valid topics")

    return validated


def _fallback_rank_items(items: list[dict]) -> list[dict]:
    hn_items = [item for item in items if item.get("source") == "hackernews"]
    gh_items = [item for item in items if item.get("source") == "github"]

    hn_sorted = sorted(
        hn_items,
        key=lambda x: (int(x.get("points", 0)), int(x.get("num_comments", 0))),
        reverse=True,
    )
    gh_sorted = sorted(
        gh_items,
        key=lambda x: len(str(x.get("description", ""))),
        reverse=True,
    )

    selected = hn_sorted[:3] + gh_sorted[:2]
    if not selected:
        raise RuntimeError("No trending items available for fallback ranking")

    ranked: list[dict] = []
    for item in selected:
        if item.get("source") == "hackernews":
            title = str(item.get("title", "")).strip()
            if not title:
                continue
            ranked.append(
                {
                    "subject": title,
                    "brief": (
                        "Explain why this topic is trending, break down the core technical "
                        "ideas, and include practical takeaways for developers."
                    ),
                    "source": "hackernews",
                }
            )
        else:
            name = str(item.get("name", "")).strip()
            description = str(item.get("description", "")).strip()
            if not name:
                continue
            ranked.append(
                {
                    "subject": f"What developers can learn from {name}",
                    "brief": (
                        f"Analyze {name} and its engineering decisions. "
                        f"Focus on implementation patterns and developer lessons. {description}".strip()
                    ),
                    "source": "github",
                }
            )

    if not ranked:
        raise RuntimeError("Fallback ranking produced no valid topics")

    return ranked


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

    raw = message.content[0].text if message.content else ""
    try:
        ranked = _parse_ranked_topics(raw)
    except (json.JSONDecodeError, ValueError, TypeError, AttributeError) as exc:
        logger.warning("AI ranking parse failed (%s). Falling back to deterministic ranking.", exc)
        ranked = _fallback_rank_items(items)

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
