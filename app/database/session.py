from collections.abc import AsyncIterator
from uuid import UUID

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import ORMExecuteState, Session, with_loader_criteria
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

settings = get_settings()
if settings.app_env == "test":
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
else:
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)

session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


@event.listens_for(Session, "do_orm_execute")
def apply_tenant_scope(execute_state: ORMExecuteState) -> None:
    """Aplica uma segunda barreira de isolamento às consultas autenticadas."""
    organization_id = execute_state.session.info.get("organization_id")
    if organization_id is None or not execute_state.is_select:
        return
    if not isinstance(organization_id, UUID):
        raise TypeError("organization_id da sessão deve ser UUID")

    from app.models.organization import Organization
    from app.models.user import User

    execute_state.statement = execute_state.statement.options(
        with_loader_criteria(
            Organization,
            lambda model: model.id == organization_id,
            include_aliases=True,
        ),
        with_loader_criteria(
            User,
            lambda model: model.organization_id == organization_id,
            include_aliases=True,
        ),
    )


async def get_session() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session
