#!/bin/sh
set -eu
umask 077

backup_dir=${BACKUP_DIR:-backups}
timestamp=$(date -u +%Y%m%d-%H%M%S)
database=${POSTGRES_DB:-relayguard}
user=${POSTGRES_USER:-relayguard}
destination="$backup_dir/relayguard-$timestamp.sql.gz"
temporary="$backup_dir/.relayguard-$timestamp.sql"

mkdir -p "$backup_dir"
trap 'rm -f "$temporary"' EXIT HUP INT TERM

docker compose exec -T db pg_dump \
    --clean \
    --if-exists \
    --no-owner \
    --no-privileges \
    --username "$user" \
    "$database" > "$temporary"

test -s "$temporary"
gzip -9 < "$temporary" > "$destination"
gzip -t "$destination"
rm -f "$temporary"
trap - EXIT HUP INT TERM

printf '%s\n' "Backup criado e validado: $destination"
