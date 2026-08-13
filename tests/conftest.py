from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.database.session import session_factory
from app.main import app
from app.models.organization import Organization
from app.models.user import User


async def clean_test_identity_data() -> None:
    async with session_factory() as session:
        await session.execute(delete(User).where(User.email.like("%@example.com")))
        await session.execute(
            delete(Organization).where(Organization.slug.like("test-%"))
        )
        await session.commit()


@pytest_asyncio.fixture(autouse=True)
async def identity_database_cleanup() -> AsyncIterator[None]:
    await clean_test_identity_data()
    yield
    await clean_test_identity_data()


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as value:
        yield value
