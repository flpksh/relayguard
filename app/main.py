from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.organizations import router as organizations_router
from app.api.users import router as users_router
from app.core.config import get_settings
from app.database.session import engine


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="0.2.0",
        lifespan=lifespan,
    )
    application.include_router(health_router, prefix="/health", tags=["health"])
    application.include_router(auth_router, tags=["authentication"])
    application.include_router(organizations_router, tags=["organizations"])
    application.include_router(users_router, tags=["users"])
    return application


app = create_app()
