#!/usr/bin/env bash
set -euo pipefail

postgres_user="${POSTGRES_USER:?Set POSTGRES_USER}"
source_db="${POSTGRES_DB:?Set POSTGRES_DB}"
drill_db="${source_db}_restore_drill_$(date -u +%Y%m%d%H%M%S)_${RANDOM}"
drill_dir="$(mktemp -d)"

cleanup() {
  docker compose exec -T postgres dropdb \
    --username "${postgres_user}" --if-exists "${drill_db}" >/dev/null
  rm -rf "${drill_dir}"
}
trap cleanup EXIT

BACKUP_DIR="${drill_dir}" scripts/backup-postgres.sh
backup_file="$(find "${drill_dir}" -maxdepth 1 -name '*.dump' -type f -print -quit)"
test -n "${backup_file}"

docker compose exec -T postgres createdb \
  --username "${postgres_user}" "${drill_db}"

CONFIRM_RESTORE=YES POSTGRES_DB="${drill_db}" \
  scripts/restore-postgres.sh "${backup_file}"

source_version="$(docker compose exec -T postgres psql --username "${postgres_user}" \
  --dbname "${source_db}" --tuples-only --no-align \
  --command 'SELECT version_num FROM alembic_version')"
restored_version="$(docker compose exec -T postgres psql --username "${postgres_user}" \
  --dbname "${drill_db}" --tuples-only --no-align \
  --command 'SELECT version_num FROM alembic_version')"
source_tables="$(docker compose exec -T postgres psql --username "${postgres_user}" \
  --dbname "${source_db}" --tuples-only --no-align \
  --command "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")"
restored_tables="$(docker compose exec -T postgres psql --username "${postgres_user}" \
  --dbname "${drill_db}" --tuples-only --no-align \
  --command "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")"

test -n "${source_version}"
test "${source_version}" = "${restored_version}"
test "${source_tables}" = "${restored_tables}"

printf 'BACKUP_RESTORE_DRILL_OK database=%s migration=%s tables=%s\n' \
  "${drill_db}" "${restored_version}" "${restored_tables}"
