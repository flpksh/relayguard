import json
import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from time import perf_counter
from uuid import UUID, uuid4

from starlette.requests import Request
from starlette.responses import Response


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in (
            "event",
            "request_id",
            "method",
            "path",
            "status_code",
            "duration_ms",
            "user_id",
            "organization_id",
        ):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    logger = logging.getLogger("relayguard")
    if logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def _request_id(request: Request) -> str:
    candidate = request.headers.get("X-Request-ID")
    if candidate:
        try:
            return str(UUID(candidate))
        except ValueError:
            pass
    return str(uuid4())


async def request_observability_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = _request_id(request)
    started_at = perf_counter()
    logger = logging.getLogger("relayguard.http")
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "requisição não tratada",
            extra={
                "event": "request.failed",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
            },
        )
        raise
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "requisição concluída",
        extra={
            "event": "request.completed",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round((perf_counter() - started_at) * 1000, 2),
        },
    )
    return response


def audit(event: str, **fields: str) -> None:
    logging.getLogger("relayguard.audit").info(
        "evento de auditoria", extra={"event": event, **fields}
    )
