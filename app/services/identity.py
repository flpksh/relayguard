from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.observability import audit
from app.core.security import hash_password, verify_password
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.organization import OrganizationUpdate
from app.schemas.user import UserCreate

DUMMY_PASSWORD_HASH = hash_password("dummy-password-used-to-equalize-login-timing")


def normalize_email(email: str) -> str:
    return email.strip().lower()


def constraint_name(error: IntegrityError) -> str | None:
    original = error.orig
    cause = getattr(original, "__cause__", None)
    value = getattr(cause, "constraint_name", None) or getattr(
        original, "constraint_name", None
    )
    return value if isinstance(value, str) else None


async def register_owner(
    session: AsyncSession, payload: RegisterRequest
) -> tuple[Organization, User]:
    organization = Organization(
        name=payload.organization_name,
        slug=payload.organization_slug,
    )
    owner = User(
        organization=organization,
        email=normalize_email(str(payload.email)),
        password_hash=hash_password(payload.password),
        role=UserRole.OWNER.value,
    )
    session.add_all([organization, owner])
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        constraint = constraint_name(error)
        if constraint == "ix_organizations_slug":
            raise ConflictError("o slug da organização já existe") from error
        if constraint == "ix_users_email":
            raise ConflictError("o e-mail já existe") from error
        raise
    audit(
        "identity.owner_registered",
        user_id=str(owner.id),
        organization_id=str(organization.id),
    )
    return organization, owner


async def authenticate_user(
    session: AsyncSession, payload: LoginRequest
) -> tuple[Organization, User]:
    user = await UserRepository.get_by_email(
        session, normalize_email(str(payload.email))
    )
    password_hash = user.password_hash if user is not None else DUMMY_PASSWORD_HASH
    password_is_valid = verify_password(payload.password, password_hash)
    if user is None or not user.is_active or not password_is_valid:
        raise AuthenticationError("credenciais inválidas")
    return user.organization, user


async def update_organization(
    session: AsyncSession,
    organization: Organization,
    payload: OrganizationUpdate,
) -> Organization:
    organization.name = payload.name
    await session.commit()
    await session.refresh(organization)
    audit(
        "identity.organization_updated",
        organization_id=str(organization.id),
    )
    return organization


async def create_member(
    session: AsyncSession, organization: Organization, payload: UserCreate
) -> User:
    member = User(
        organization=organization,
        email=normalize_email(str(payload.email)),
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    session.add(member)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        if constraint_name(error) == "ix_users_email":
            raise ConflictError("o e-mail já existe") from error
        raise
    audit(
        "identity.member_created",
        user_id=str(member.id),
        organization_id=str(organization.id),
    )
    return member


async def revoke_user_tokens(session: AsyncSession, user: User) -> None:
    user.token_version += 1
    await session.commit()
    audit(
        "identity.tokens_revoked",
        user_id=str(user.id),
        organization_id=str(user.organization_id),
    )
