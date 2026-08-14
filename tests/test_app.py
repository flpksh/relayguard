from uuid import UUID

from fastapi import FastAPI
from httpx import AsyncClient

from app.main import create_app


def test_application_factory() -> None:
    application = create_app()
    assert isinstance(application, FastAPI)
    assert application.title == "RelayGuard"
    assert application.version == "0.2.0"
    paths = application.openapi()["paths"]
    assert "/health/live" in paths
    assert "/health/ready" in paths
    assert "/auth/register" in paths
    assert "/auth/login" in paths
    assert "/auth/me" in paths
    assert "/auth/logout" in paths
    assert "/organizations/current" in paths
    assert "/users" in paths


async def test_request_id_is_returned(client: AsyncClient) -> None:
    response = await client.get(
        "/health/live", headers={"X-Request-ID": "valor-invalido"}
    )

    assert response.status_code == 200
    assert UUID(response.headers["X-Request-ID"])
