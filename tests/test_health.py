from httpx import AsyncClient
from pytest import MonkeyPatch
from sqlalchemy.exc import OperationalError

from app.api import health


class UnavailableDatabase:
    async def __aenter__(self) -> None:
        raise OperationalError("SELECT 1", {}, RuntimeError("offline"))

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object,
    ) -> None:
        return None


async def test_liveness(client: AsyncClient) -> None:
    response = await client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": None}


async def test_readiness(client: AsyncClient) -> None:
    response = await client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


async def test_readiness_when_database_is_unavailable(
    client: AsyncClient, monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setattr(health, "session_factory", UnavailableDatabase)
    response = await client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {"detail": "database unavailable"}
