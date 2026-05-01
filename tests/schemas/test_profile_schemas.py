from datetime import datetime, timezone

from app.schemas.profile import LinkedInStatusResponse, ProfileResponse, ProfileUpdate


def test_profile_update_defaults():
    profile = ProfileUpdate(
        name="Matias Ruiz",
        headline="Software Engineer",
        bio="Building things.",
    )
    assert profile.avatar_url is None
    assert profile.location is None
    assert profile.skills == []
    assert profile.links == {}


def test_profile_response_has_no_linkedin_fields():
    fields = ProfileResponse.model_fields
    assert "linkedin" not in fields
    assert "linkedin_access_token" not in fields
    assert "linkedin_last_synced_at" not in fields


def test_profile_response_from_attributes():
    class FakeProfile:
        id = "prof123"
        name = "Matias Ruiz"
        headline = "Engineer"
        bio = "Bio text."
        avatar_url = None
        location = "Madrid"
        skills = ["Python"]
        links = {"github": "https://github.com/matiasruiz"}
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)

    response = ProfileResponse.model_validate(FakeProfile())
    assert response.id == "prof123"
    assert response.location == "Madrid"
    assert response.skills == ["Python"]


def test_linkedin_status_response_not_connected():
    status = LinkedInStatusResponse(connected=False)
    assert status.linkedin_id is None
    assert status.token_expires_at is None
    assert status.last_synced_at is None


def test_linkedin_status_response_connected():
    now = datetime.now(timezone.utc)
    status = LinkedInStatusResponse(
        connected=True,
        linkedin_id="urn:li:person:123",
        token_expires_at=now,
        last_synced_at=now,
    )
    assert status.connected is True
    assert status.linkedin_id == "urn:li:person:123"
