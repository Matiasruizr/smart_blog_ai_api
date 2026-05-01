from app.models.profile import Profile
from app.schemas.profile import LinkedInStatusResponse, ProfileUpdate


async def get() -> Profile | None:
    return await Profile.find_one()


async def upsert(data: ProfileUpdate) -> Profile:
    profile = await Profile.find_one()
    if profile is None:
        profile = Profile(
            name=data.name,
            headline=data.headline,
            bio=data.bio,
            avatar_url=data.avatar_url,
            location=data.location,
            skills=data.skills,
            links=data.links,
        )
        await profile.insert()
    else:
        profile.name = data.name
        profile.headline = data.headline
        profile.bio = data.bio
        profile.avatar_url = data.avatar_url
        profile.location = data.location
        profile.skills = data.skills
        profile.links = data.links
        await profile.replace()
    return profile


def get_linkedin_status(profile: Profile) -> LinkedInStatusResponse:
    if profile.linkedin is None:
        return LinkedInStatusResponse(connected=False)
    return LinkedInStatusResponse(
        connected=True,
        linkedin_id=profile.linkedin.linkedin_id,
        token_expires_at=profile.linkedin.token_expires_at,
        last_synced_at=profile.linkedin.last_synced_at,
    )
