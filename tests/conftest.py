from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.core.config import get_settings
from app.core.rate_limit import auth_rate_limiter
from app.database.session import session_factory
from app.main import app
from app.models.organization import Organization
from app.models.user import User


async def clean_test_identity_data() -> None:
    settings = get_settings()
    if settings.app_env != "test" or not settings.database_url.endswith(
        "/relayguard_test"
    ):
        raise RuntimeError("os testes de identidade exigem o banco relayguard_test")
    async with session_factory() as session:
        await session.execute(delete(User))
        await session.execute(delete(Organization))
        await session.commit()


@pytest_asyncio.fixture(autouse=True)
async def identity_database_cleanup() -> AsyncIterator[None]:
    auth_rate_limiter.reset()
    await clean_test_identity_data()
    yield
    await clean_test_identity_data()
    auth_rate_limiter.reset()


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as value:
        yield value
