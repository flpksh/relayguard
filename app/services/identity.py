from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, ConflictError
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
        raise ConflictError("organization slug or email already exists") from error
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
        raise AuthenticationError("invalid credentials")
    return user.organization, user


async def update_organization(
    session: AsyncSession,
    organization: Organization,
    payload: OrganizationUpdate,
) -> Organization:
    organization.name = payload.name
    await session.commit()
    await session.refresh(organization)
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
        raise ConflictError("email already exists") from error
    return member
