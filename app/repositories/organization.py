from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization


class OrganizationRepository:
    @staticmethod
    async def get_by_id(
        session: AsyncSession, organization_id: UUID
    ) -> Organization | None:
        return await session.get(Organization, organization_id)

    @staticmethod
    async def get_by_slug(session: AsyncSession, slug: str) -> Organization | None:
        result = await session.execute(
            select(Organization).where(Organization.slug == slug)
        )
        return result.scalar_one_or_none()
