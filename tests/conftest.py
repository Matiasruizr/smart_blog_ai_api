import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.models.post import BlogPost
from app.models.profile import Profile


@pytest_asyncio.fixture
async def db():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    database = client["test_smart_blog_ai"]
    await init_beanie(database=database, document_models=[BlogPost, Profile])
    yield database
    await client.drop_database("test_smart_blog_ai")
    client.close()
