# RelayGuard

RelayGuard será uma plataforma multi-tenant para entrega confiável e observável de webhooks. A Etapa 1 estabelece a fundação executável: API FastAPI, PostgreSQL assíncrono, migrações Alembic, contêineres e ferramentas de qualidade.

## Executar localmente

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec api alembic upgrade head
curl --fail http://localhost:8000/health/live
curl --fail http://localhost:8000/health/ready
```

## Qualidade

```bash
docker compose exec api pytest --cov=app --cov-report=term-missing
docker compose exec api ruff check .
docker compose exec api mypy app tests
```

## Endpoints da fundação

- `GET /health/live`: confirma que o processo da API está vivo.
- `GET /health/ready`: confirma que a API consegue consultar o PostgreSQL.
- `GET /docs`: documentação OpenAPI interativa.

O escopo e as decisões da etapa estão registrados em `docs/RELATORIO_ETAPA_01.md`.
