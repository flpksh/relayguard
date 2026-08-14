# RelayGuard

RelayGuard será uma plataforma multi-tenant para entrega confiável e observável
de webhooks. A Etapa 1 estabeleceu a fundação executável. A Etapa 2 introduz a
fronteira de identidade: organizações, usuários, autenticação e isolamento entre
tenants.

## Executar localmente

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec api alembic upgrade head
curl --fail http://localhost:8010/health/live
curl --fail http://localhost:8010/health/ready
```

Antes de usar em produção, altere `ACCESS_TOKEN_SECRET` e as credenciais do
PostgreSQL. O segredo do token deve ter ao menos 32 caracteres.

## Fluxo inicial da Etapa 2

1. `POST /auth/register` cria uma organização e seu proprietário.
2. `POST /auth/login` autentica por e-mail e senha.
3. Envie `Authorization: Bearer <token>` aos endpoints protegidos.
4. `GET /auth/me` retorna o usuário autenticado.
5. `GET /organizations/current` retorna a organização do token.
6. `PATCH /organizations/current` altera seu nome, somente como proprietário.
7. `GET /users` lista apenas usuários da organização atual.
8. `POST /users` cria um membro, somente como proprietário.
9. `POST /auth/logout` revoga imediatamente os tokens atuais do usuário.

A especificação interativa completa permanece disponível em `GET /docs`.
A listagem de usuários aceita `limit` (1 a 100) e `offset`.

## Qualidade

```bash
docker compose exec api alembic upgrade head
docker compose --profile quality run --build --rm quality
docker compose --profile quality run --build --rm quality ruff check app tests migrations
docker compose --profile quality run --build --rm quality ruff format --check app tests migrations
docker compose --profile quality run --build --rm quality mypy app tests
```

Os testes usam um PostgreSQL temporário e separado do banco de desenvolvimento.

## Endpoints de saúde

- `GET /health/live`: confirma que o processo da API está vivo.
- `GET /health/ready`: confirma que a API consegue consultar o PostgreSQL.

## Documentação de etapas

- `docs/RELATORIO_ETAPA_01.md`: fundação executável.
- `docs/ETAPA_02_ESCOPO.md`: identidade e multi-tenancy.

## Organização local

O repositório continua se chamando RelayGuard e usa
`https://github.com/flpksh/relayguard`. A pasta local pode se chamar `rgwh`; o
nome do projeto Docker permanece `relayguard` por `COMPOSE_PROJECT_NAME`.

A API usa a porta externa `8010` por padrão para poder executar ao mesmo tempo
que o projeto `api_cnpj`, que usa `8000`. Altere `HOST_PORT` no `.env` quando
necessário.

Em produção, forneça `DATABASE_URL`, `ACCESS_TOKEN_SECRET` e as credenciais por
um gerenciador de segredos.

Para rotacionar a chave JWT sem interromper tokens ainda válidos, configure o
novo valor em `ACCESS_TOKEN_SECRET` e mantenha temporariamente o anterior em
`ACCESS_TOKEN_PREVIOUS_SECRET`. Remova o segredo anterior após o prazo máximo dos
tokens.

## Operação e backups

As orientações de backup, restauração, limites de recursos e recuperação estão em
`docs/OPERACAO.md`. O script `scripts/backup_database.sh` cria um backup comprimido
e valida sua integridade.
