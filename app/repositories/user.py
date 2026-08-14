from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User


class UserRepository:
    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: UUID) -> User | None:
        return await session.get(User, user_id)

    @staticmethod
    async def get_by_email(session: AsyncSession, email: str) -> User | None:
        result = await session.execute(
            select(User)
            .options(selectinload(User.organization))
            .where(User.email == email)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_for_organization(
        session: AsyncSession,
        organization_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[User]:
        result = await session.execute(
            select(User)
            .where(User.organization_id == organization_id)
            .order_by(User.created_at, User.id)
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
