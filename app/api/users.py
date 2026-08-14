from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import CurrentUserDep, OwnerDep, SessionDep
from app.core.exceptions import ConflictError
from app.repositories.organization import OrganizationRepository
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserResponse
from app.services.identity import create_member

router = APIRouter(prefix="/users")


@router.get("", response_model=list[UserResponse])
async def list_users(
    user: CurrentUserDep,
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[UserResponse]:
    users = await UserRepository.list_for_organization(
        session,
        user.organization_id,
        limit=limit,
        offset=offset,
    )
    return [UserResponse.model_validate(value) for value in users]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def add_member(
    payload: UserCreate, owner: OwnerDep, session: SessionDep
) -> UserResponse:
    organization = await OrganizationRepository.get_by_id(
        session, owner.organization_id
    )
    if organization is None:
        raise HTTPException(status_code=404, detail="organização não encontrada")
    try:
        member = await create_member(session, organization, payload)
    except ConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return UserResponse.model_validate(member)
