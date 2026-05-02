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

    mongodb_uri: str
    mongodb_db_name: str

    ai_model: str = "claude-sonnet-4-6"
    access_token_expire_minutes: int = 1440

    linkedin_client_id: str = ""
    linkedin_client_secret: str = ""
    linkedin_redirect_uri: str = "http://localhost:8000/api/v1/linkedin/callback"
    linkedin_scope: str = "r_liteprofile w_member_social"
    frontend_url: str = "http://localhost:3000"
    blog_url: str = "http://localhost:3000"

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
