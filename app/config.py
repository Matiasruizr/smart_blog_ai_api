from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    secret_key: str
    allowed_origins: list[str] = ["http://localhost:3000"]
    api_v1_prefix: str = "/api/v1"

    owner_username: str = "admin"
    owner_password_hash: str = ""

    mongodb_uri: str
    mongodb_db_name: str

    anthropic_api_key: str = ""
    ai_model: str = "claude-sonnet-4-6"
    ai_max_tokens: int = 4096
    access_token_expire_minutes: int = 1440

    unsplash_access_key: str = ""
    pexels_api_key: str = ""

    linkedin_client_id: str = ""
    linkedin_client_secret: str = ""
    linkedin_redirect_uri: str = "http://localhost:8000/api/v1/linkedin/callback"
    linkedin_scope: str = "r_liteprofile w_member_social"
    frontend_url: str = "http://localhost:3000"
    blog_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:8000"

    scheduler_enabled: bool = True
    automation_interval_hours: int = 48

    email_provider: str = "smtp"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    sendgrid_api_key: str = ""
    email_from: str = ""
    email_to_owner: str = ""

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, v: object) -> object:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


SettingsDep = Annotated[Settings, Depends(get_settings)]
