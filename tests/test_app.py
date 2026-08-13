from fastapi import FastAPI

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
    assert "/organizations/current" in paths
    assert "/users" in paths
