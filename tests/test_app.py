from fastapi import FastAPI

from app.main import create_app


def test_application_factory() -> None:
    application = create_app()
    assert isinstance(application, FastAPI)
    assert application.title == "RelayGuard"
    paths = application.openapi()["paths"]
    assert "/health/live" in paths
    assert "/health/ready" in paths
