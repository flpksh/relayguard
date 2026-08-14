from fastapi import APIRouter, HTTPException, Request, Response, status

from app.api.dependencies import CurrentUserDep, SessionDep
from app.core.config import get_settings
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.rate_limit import (
    RateLimitExceeded,
    RateLimitRule,
    auth_rate_limiter,
)
from app.core.security import create_access_token
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from app.schemas.user import UserResponse
from app.services.identity import (
    authenticate_user,
    normalize_email,
    register_owner,
    revoke_user_tokens,
)

router = APIRouter(prefix="/auth")


async def enforce_auth_rate_limit(
    request: Request, action: str, identifier: str | None = None
) -> None:
    settings = get_settings()
    client_host = request.client.host if request.client is not None else "desconhecido"
    rule = RateLimitRule(
        requests=settings.auth_rate_limit_requests,
        window_seconds=settings.auth_rate_limit_window_seconds,
    )
    try:
        await auth_rate_limiter.check(f"{action}:origem:{client_host}", rule)
        if identifier is not None:
            await auth_rate_limiter.check(f"{action}:identidade:{identifier}", rule)
    except RateLimitExceeded as error:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="muitas tentativas; tente novamente mais tarde",
            headers={"Retry-After": str(error.retry_after)},
        ) from error


@router.post(
    "/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    payload: RegisterRequest, session: SessionDep, request: Request
) -> AuthResponse:
    await enforce_auth_rate_limit(request, "cadastro")
    try:
        organization, owner = await register_owner(session, payload)
    except ConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return AuthResponse(
        access_token=create_access_token(
            owner.id, organization.id, owner.token_version
        ),
        user=UserResponse.model_validate(owner),
        organization=organization,
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest, session: SessionDep, request: Request
) -> AuthResponse:
    await enforce_auth_rate_limit(request, "login", normalize_email(str(payload.email)))
    try:
        organization, user = await authenticate_user(session, payload)
    except AuthenticationError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="e-mail ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    return AuthResponse(
        access_token=create_access_token(user.id, organization.id, user.token_version),
        user=UserResponse.model_validate(user),
        organization=organization,
    )


@router.get("/me", response_model=UserResponse)
async def me(user: CurrentUserDep) -> UserResponse:
    return UserResponse.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(user: CurrentUserDep, session: SessionDep) -> Response:
    await revoke_user_tokens(session, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
