from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database.session import session_factory

router = APIRouter()


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    database: Literal["connected"] | None = None


@router.get("/live", response_model=HealthResponse)
async def liveness() -> HealthResponse:
    return HealthResponse()


@router.get("/ready", response_model=HealthResponse)
async def readiness() -> HealthResponse:
    try:
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="banco de dados indisponível",
        ) from exc
    return HealthResponse(database="connected")
