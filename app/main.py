from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app import __version__
from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.organizations import router as organizations_router
from app.api.users import router as users_router
from app.core.config import get_settings
from app.core.observability import configure_logging, request_observability_middleware
from app.database.session import engine


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await engine.dispose()


async def validation_error_handler(_: Request, exception: Exception) -> JSONResponse:
    error = exception if isinstance(exception, RequestValidationError) else None
    assert error is not None
    errors = [
        {"location": item["loc"], "type": item["type"]} for item in error.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder(
            {"detail": "dados da requisição inválidos", "errors": errors}
        ),
    )


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()
    application = FastAPI(
        title=settings.app_name,
        version=__version__,
        lifespan=lifespan,
    )
    application.middleware("http")(request_observability_middleware)
    application.add_exception_handler(RequestValidationError, validation_error_handler)
    application.include_router(health_router, prefix="/health", tags=["health"])
    application.include_router(auth_router, tags=["authentication"])
    application.include_router(organizations_router, tags=["organizations"])
    application.include_router(users_router, tags=["users"])
    return application


app = create_app()
