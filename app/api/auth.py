from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentUserDep, SessionDep
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import create_access_token
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from app.schemas.user import UserResponse
from app.services.identity import authenticate_user, register_owner

router = APIRouter(prefix="/auth")


@router.post(
    "/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED
)
async def register(payload: RegisterRequest, session: SessionDep) -> AuthResponse:
    try:
        organization, owner = await register_owner(session, payload)
    except ConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return AuthResponse(
        access_token=create_access_token(owner.id, organization.id),
        user=UserResponse.model_validate(owner),
        organization=organization,
    )


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, session: SessionDep) -> AuthResponse:
    try:
        organization, user = await authenticate_user(session, payload)
    except AuthenticationError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    return AuthResponse(
        access_token=create_access_token(user.id, organization.id),
        user=UserResponse.model_validate(user),
        organization=organization,
    )


@router.get("/me", response_model=UserResponse)
async def me(user: CurrentUserDep) -> UserResponse:
    return UserResponse.model_validate(user)
