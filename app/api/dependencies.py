from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.database.session import get_session
from app.models.user import User, UserRole
from app.repositories.user import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)
SessionDep = Annotated[AsyncSession, Depends(get_session)]


def credentials_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: SessionDep,
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise credentials_error()
    claims = decode_access_token(credentials.credentials)
    if claims is None:
        raise credentials_error()
    session.info["organization_id"] = claims.organization_id
    user = await UserRepository.get_by_id(session, claims.user_id)
    if (
        user is None
        or not user.is_active
        or user.organization_id != claims.organization_id
        or user.token_version != claims.token_version
    ):
        raise credentials_error()
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


async def require_owner(user: CurrentUserDep) -> User:
    if user.role != UserRole.OWNER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="é necessário ser proprietário da organização",
        )
    return user


OwnerDep = Annotated[User, Depends(require_owner)]
