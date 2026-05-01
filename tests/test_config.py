from app.config import Settings


def test_settings_defaults():
    settings = Settings(
        secret_key="test-secret-at-least-32-chars-long-yes",
        mongodb_uri="mongodb://localhost:27017",
        mongodb_db_name="test_db",
    )
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.ai_model == "claude-sonnet-4-6"
    assert settings.access_token_expire_minutes == 1440
    assert isinstance(settings.allowed_origins, list)


def test_settings_allowed_origins_parsed_from_string():
    settings = Settings(
        secret_key="test-secret-at-least-32-chars-long-yes",
        mongodb_uri="mongodb://localhost:27017",
        mongodb_db_name="test_db",
        allowed_origins="http://localhost:3000,https://myblog.com",
    )
    assert settings.allowed_origins == ["http://localhost:3000", "https://myblog.com"]
