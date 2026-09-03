#!/usr/bin/env bash
set -euo pipefail

umask 077

backup_dir="${BACKUP_DIR:-./backups}"
postgres_user="${POSTGRES_USER:?Set POSTGRES_USER}"
postgres_db="${POSTGRES_DB:?Set POSTGRES_DB}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_file="${backup_dir}/cybersentinel-${timestamp}.dump"

mkdir -p "${backup_dir}"

docker compose exec -T postgres \
  pg_dump --username "${postgres_user}" --dbname "${postgres_db}" \
  --format custom --no-owner --no-privileges >"${backup_file}"

test -s "${backup_file}"
docker compose exec -T postgres pg_restore --list <"${backup_file}" >/dev/null
sha256sum "${backup_file}" >"${backup_file}.sha256"

printf 'Backup verified: %s\n' "${backup_file}"
