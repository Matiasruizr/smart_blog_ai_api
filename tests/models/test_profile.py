import asyncio
from datetime import datetime

from app.models.profile import LinkedInCredentials, Profile


async def test_profile_defaults(db):
    profile = Profile(
        name="Matias Ruiz",
        headline="Software Engineer",
        bio="Building things with Python and AI.",
    )
    await profile.insert()

    assert profile.avatar_url is None
    assert profile.location is None
    assert profile.skills == []
    assert profile.links == {}
    assert profile.linkedin is None
    assert isinstance(profile.created_at, datetime)
    assert isinstance(profile.updated_at, datetime)
    assert profile.id is not None


async def test_profile_with_linkedin_credentials(db):
    creds = LinkedInCredentials(
        access_token="token-abc",
        refresh_token="refresh-xyz",
        token_expires_at=datetime.utcnow(),
        linkedin_id="urn:li:person:123",
    )
    profile = Profile(
        name="Matias Ruiz",
        headline="Engineer",
        bio="Bio text.",
        skills=["Python", "FastAPI"],
        links={"github": "https://github.com/matiasruiz"},
        linkedin=creds,
    )
    await profile.insert()

    assert profile.linkedin is not None
    assert profile.linkedin.access_token == "token-abc"
    assert profile.linkedin.linkedin_id == "urn:li:person:123"
    assert profile.linkedin.last_synced_at is None


async def test_profile_linkedin_can_be_cleared(db):
    creds = LinkedInCredentials(
        access_token="token-abc",
        linkedin_id="urn:li:person:123",
    )
    profile = Profile(
        name="Matias Ruiz",
        headline="Engineer",
        bio="Bio.",
        linkedin=creds,
    )
    await profile.insert()

    profile.linkedin = None
    await profile.replace()

    refreshed = await Profile.get(profile.id)
    assert refreshed.linkedin is None


async def test_updated_at_changes_on_replace(db):
    profile = Profile(
        name="Matias Ruiz",
        headline="Engineer",
        bio="Bio.",
    )
    await profile.insert()
    original_updated_at = profile.updated_at

    await asyncio.sleep(0.01)
    profile.name = "Changed Name"
    await profile.replace()

    assert profile.updated_at > original_updated_at
