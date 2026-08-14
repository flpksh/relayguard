from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.api.dependencies import CurrentUserDep, OwnerDep, SessionDep
from app.models.organization import Organization
from app.repositories.organization import OrganizationRepository
from app.schemas.organization import OrganizationResponse, OrganizationUpdate
from app.services.identity import update_organization

router = APIRouter(prefix="/organizations")


async def load_organization(session: SessionDep, organization_id: UUID) -> Organization:
    organization = await OrganizationRepository.get_by_id(session, organization_id)
    if organization is None:
        raise HTTPException(status_code=404, detail="organização não encontrada")
    return organization


@router.get("/current", response_model=OrganizationResponse)
async def current_organization(
    user: CurrentUserDep, session: SessionDep
) -> OrganizationResponse:
    organization = await load_organization(session, user.organization_id)
    return OrganizationResponse.model_validate(organization)


@router.patch("/current", response_model=OrganizationResponse)
async def rename_organization(
    payload: OrganizationUpdate, owner: OwnerDep, session: SessionDep
) -> OrganizationResponse:
    organization = await load_organization(session, owner.organization_id)
    updated = await update_organization(session, organization, payload)
    return OrganizationResponse.model_validate(updated)
