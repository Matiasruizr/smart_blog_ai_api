from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import Settings
from app.models.post import BlogPost
from app.models.profile import Profile
from app.models.topic import TrendingTopic


async def init_db(settings: Settings) -> None:
    client = AsyncIOMotorClient(settings.mongodb_uri)
    await init_beanie(
        database=client[settings.mongodb_db_name],
        document_models=[BlogPost, Profile, TrendingTopic],
    )
