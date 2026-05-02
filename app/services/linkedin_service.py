from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx

from app.config import Settings
from app.models.post import BlogPost
from app.models.profile import LinkedInCredentials, Profile
from app.schemas.profile import TokenStatusResponse

_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
_ME_URL = "https://api.linkedin.com/v2/me"
_UGC_URL = "https://api.linkedin.com/v2/ugcPosts"


def get_auth_url(settings: Settings) -> str:
    params = {
        "response_type": "code",
        "client_id": settings.linkedin_client_id,
        "redirect_uri": settings.linkedin_redirect_uri,
        "scope": settings.linkedin_scope,
    }
    return f"{_AUTH_URL}?{urlencode(params)}"


async def exchange_code(code: str, settings: Settings) -> LinkedInCredentials:
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            _TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.linkedin_redirect_uri,
                "client_id": settings.linkedin_client_id,
                "client_secret": settings.linkedin_client_secret,
            },
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()

        access_token: str = token_data["access_token"]
        expires_in: int = token_data.get("expires_in", 5184000)
        token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        me_resp = await client.get(
            _ME_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        me_resp.raise_for_status()
        me_data = me_resp.json()

    return LinkedInCredentials(
        access_token=access_token,
        refresh_token=token_data.get("refresh_token"),
        token_expires_at=token_expires_at,
        linkedin_id=me_data["id"],
    )


async def sync_profile(profile: Profile, settings: Settings) -> Profile:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_ME_URL}?projection=(id,localizedFirstName,localizedLastName,localizedHeadline)",
            headers={"Authorization": f"Bearer {profile.linkedin.access_token}"},
        )
        resp.raise_for_status()
        data = resp.json()

    first = data.get("localizedFirstName", "")
    last = data.get("localizedLastName", "")
    profile.name = f"{first} {last}".strip()
    if data.get("localizedHeadline"):
        profile.headline = data["localizedHeadline"]
    profile.linkedin.last_synced_at = datetime.now(timezone.utc)
    await profile.replace()
    return profile


async def share_post(post: BlogPost, profile: Profile, settings: Settings) -> str:
    post_url = f"{settings.blog_url}/blog/{post.slug}"
    payload = {
        "author": f"urn:li:person:{profile.linkedin.linkedin_id}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": f"{post.title}\n\n{post.excerpt}"},
                "shareMediaCategory": "ARTICLE",
                "media": [{
                    "status": "READY",
                    "description": {"text": post.excerpt},
                    "originalUrl": post_url,
                    "title": {"text": post.title},
                }],
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _UGC_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {profile.linkedin.access_token}",
                "X-Restli-Protocol-Version": "2.0.0",
            },
        )
        resp.raise_for_status()
        ugc_id: str = resp.json()["id"]

    post_num = ugc_id.split(":")[-1]
    return f"https://www.linkedin.com/feed/update/urn:li:ugcPost:{post_num}"


def get_token_status(profile: Profile) -> TokenStatusResponse:
    if profile.linkedin is None:
        return TokenStatusResponse(valid=False)

    expires_at = profile.linkedin.token_expires_at
    if expires_at is None:
        return TokenStatusResponse(valid=True)

    now = datetime.now(timezone.utc)
    valid = expires_at > now
    expires_in_days = max(0, (expires_at - now).days)
    return TokenStatusResponse(valid=valid, expires_at=expires_at, expires_in_days=expires_in_days)
