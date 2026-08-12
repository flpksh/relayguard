# RelayGuard

RelayGuard será uma plataforma multi-tenant para entrega confiável e observável de webhooks. A Etapa 1 estabelece a fundação executável: API FastAPI, PostgreSQL assíncrono, migrações Alembic, contêineres e ferramentas de qualidade.

## Executar localmente

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec api alembic upgrade head
curl --fail http://localhost:8010/health/live
curl --fail http://localhost:8010/health/ready
```

## Qualidade

```bash
docker compose --profile quality run --rm quality
docker compose --profile quality run --rm quality ruff check .
docker compose --profile quality run --rm quality ruff format --check .
docker compose --profile quality run --rm quality mypy app tests
```

## Endpoints da fundação

- `GET /health/live`: confirma que o processo da API está vivo.
- `GET /health/ready`: confirma que a API consegue consultar o PostgreSQL.
- `GET /docs`: documentação OpenAPI interativa.

O escopo e as decisões da etapa estão registrados em `docs/RELATORIO_ETAPA_01.md`.

## Organização local

O repositório continua se chamando RelayGuard e usa
`https://github.com/flpksh/relayguard`. A pasta local pode se chamar `rgwh`; o
nome do projeto Docker permanece `relayguard` por `COMPOSE_PROJECT_NAME`.

A API usa a porta externa `8010` por padrão para poder executar ao mesmo tempo
que o projeto `api_cnpj`, que usa `8000`. Altere `HOST_PORT` no `.env`
quando necessário.

Em produção, substitua as credenciais de desenvolvimento do PostgreSQL e
forneça `DATABASE_URL` por um gerenciador de segredos.
