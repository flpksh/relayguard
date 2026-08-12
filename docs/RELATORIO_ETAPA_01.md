# Relatório da Etapa 1 — Fundação

## Objetivo

Criar uma base pequena, reproduzível e verificável para o RelayGuard antes da implementação do domínio. A etapa evita introduzir autenticação, multi-tenancy e mensageria sobre uma infraestrutura ainda não validada.

## O que foi implementado

- Application factory do FastAPI e ciclo de vida explícito.
- Configuração tipada por variáveis de ambiente.
- Engine e sessões assíncronas do SQLAlchemy para PostgreSQL.
- Endpoints separados de liveness e readiness.
- Alembic com uma revisão baseline inicial.
- Imagem Docker multi-stage executada por usuário sem privilégios.
- Docker Compose com API, PostgreSQL, health checks e volume persistente.
- Testes automatizados, cobertura mínima de 85%, Ruff e Mypy estrito.
- Documentação de execução e arquivos de ambiente seguros.

## Como foi implementado

A aplicação usa uma factory para permitir criação previsível em testes e futuras configurações. O liveness não depende de serviços externos; o readiness executa `SELECT 1` usando uma sessão assíncrona. O Compose só inicia a API depois que o PostgreSQL passa no health check. As dependências e configurações das ferramentas estão centralizadas no `pyproject.toml`.

## Por que essas decisões foram tomadas

- **Monólito modular:** mantém baixo custo operacional e fronteiras claras sem microsserviços prematuros.
- **PostgreSQL assíncrono:** combina o modelo concorrente do FastAPI com o banco planejado para eventos e tentativas.
- **Liveness e readiness separados:** evita reiniciar um processo saudável apenas porque uma dependência está temporariamente indisponível.
- **Migração baseline:** comprova o fluxo de migrações antes da inclusão das tabelas de domínio.
- **Contêiner não-root:** reduz o impacto de uma eventual exploração da aplicação.
- **Qualidade como bloqueio:** impede que etapas futuras se apoiem em código que já contém erros estáticos ou regressões.

## Validação real no WSL

Validação executada em 11 de agosto de 2026 no WSL Ubuntu:

- Docker 29.5.2 e Docker Compose v5.1.4 disponíveis.
- Imagens construídas e serviços api e db iniciados com sucesso.
- PostgreSQL e API marcados como saudáveis pelo Docker Compose.
- Migração 20260811_0001 aplicada no PostgreSQL pelo Alembic.
- GET /health/live: HTTP 200 com status ok e sem dependência do banco.
- GET /health/ready: HTTP 200 com banco conectado.
- Pytest: 5 testes aprovados.
- Cobertura: 87,93%, superior ao mínimo obrigatório de 85%.
- Ruff: nenhuma violação encontrada.
- Mypy estrito: nenhum erro encontrado em 18 arquivos-fonte.

Durante a primeira validação, o usuário não-root não podia criar arquivos temporários de cobertura e cache em /app. O Dockerfile foi corrigido para transferir a propriedade do diretório de trabalho ao usuário da aplicação. Depois da reconstrução, todas as verificações foram repetidas com sucesso.

## Limites conscientes da etapa

Ainda não existem organizações, usuários, autenticação, aplicações, endpoints de destino, eventos, filas ou retentativas. Esses elementos pertencem às próximas etapas e não foram antecipados para manter a entrega auditável.
