from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.routers.automation import router as automation_router
from app.routers.linkedin import router as linkedin_router
from app.routers.post import router as post_router
from app.routers.profile import router as profile_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    await init_db(settings)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(post_router, prefix=settings.api_v1_prefix)
    app.include_router(profile_router, prefix=settings.api_v1_prefix)
    app.include_router(linkedin_router, prefix=settings.api_v1_prefix)
    app.include_router(automation_router, prefix=settings.api_v1_prefix)

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
