#!/usr/bin/env bash
set -euo pipefail

if [[ "${CONFIRM_RESTORE:-}" != "YES" ]]; then
  printf 'Refusing restore. Set CONFIRM_RESTORE=YES after verifying the target database.\n' >&2
  exit 2
fi

backup_file="${1:?Usage: restore-postgres.sh BACKUP_FILE}"
postgres_user="${POSTGRES_USER:?Set POSTGRES_USER}"
postgres_db="${POSTGRES_DB:?Set POSTGRES_DB}"

test -f "${backup_file}"
test -f "${backup_file}.sha256"
sha256sum --check "${backup_file}.sha256"

docker compose exec -T postgres pg_restore \
  --username "${postgres_user}" --dbname "${postgres_db}" \
  --clean --if-exists --no-owner --no-privileges <"${backup_file}"

printf 'Restore completed for database: %s\n' "${postgres_db}"
