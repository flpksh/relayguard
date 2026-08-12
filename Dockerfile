FROM python:3.12-slim AS builder
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
WORKDIR /build
COPY pyproject.toml .
RUN pip install --prefix=/install .

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH=/home/app/.local/bin:$PATH
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --create-home app
WORKDIR /app
COPY --from=builder /install /usr/local
COPY --chown=app:app . .
RUN chown app:app /app
USER app
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host $APP_HOST --port $APP_PORT"]

FROM runtime AS development
USER root
RUN pip install --no-cache-dir ".[dev]"
USER app
