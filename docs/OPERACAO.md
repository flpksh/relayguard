# Operação do RelayGuard

## Segredos e rotação de token

Nunca use o segredo de desenvolvimento fora do ambiente local. Em uma rotação:

1. coloque a nova chave em `ACCESS_TOKEN_SECRET`;
2. coloque a chave anterior em `ACCESS_TOKEN_PREVIOUS_SECRET`;
3. reinicie a API;
4. aguarde o maior prazo configurado para expiração dos tokens;
5. remova `ACCESS_TOKEN_PREVIOUS_SECRET` e reinicie novamente.

O endpoint `POST /auth/logout` incrementa a versão de autenticação do usuário e
invalida imediatamente todos os tokens emitidos anteriormente para ele.

## Backup

Crie um backup consistente do PostgreSQL com:

```bash
./scripts/backup_database.sh
```

O destino padrão é `backups/`, ignorado pelo Git. Também é possível informar um
diretório diferente:

```bash
BACKUP_DIR=/caminho/seguro ./scripts/backup_database.sh
```

Copie os backups para armazenamento externo com criptografia, controle de acesso
e política de retenção. Um backup mantido apenas no mesmo computador não protege
contra perda do disco.

## Restauração

Teste a restauração periodicamente em um banco descartável. Exemplo:

```bash
gunzip -c backups/relayguard-AAAAmmdd-HHMMSS.sql.gz |
  docker compose exec -T db psql -U relayguard -d relayguard
```

A restauração substitui ou combina dados conforme o conteúdo existente. Para uma
recuperação real, pare a API, valide o destino e faça uma cópia adicional antes de
executar o comando.

## Recursos e reinício

Os serviços `api` e `db` usam `restart: unless-stopped`. Os limites padrão são:

- API: 1 CPU e 512 MiB;
- PostgreSQL: 1 CPU e 512 MiB.

Ajuste `API_CPUS`, `API_MEMORY`, `DB_CPUS` e `DB_MEMORY` conforme a carga. Monitore
reinícios por falta de memória antes de reduzir os limites.

## Limite de tentativas

O limite de tentativas de cadastro e login fica em memória e atende à instância
única usada atualmente. Antes de executar múltiplas réplicas da API, substitua-o
por um armazenamento compartilhado, como Redis, para manter a contagem uniforme.
A configuração é feita por `AUTH_RATE_LIMIT_REQUESTS` e
`AUTH_RATE_LIMIT_WINDOW_SECONDS`.

## Verificações após recuperação

```bash
docker compose up -d
docker compose exec api alembic current
curl --fail http://localhost:8010/health/live
curl --fail http://localhost:8010/health/ready
```

Confirme também login, isolamento entre organizações e criação de um backup novo.
