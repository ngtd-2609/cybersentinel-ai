#!/usr/bin/env bash
set -euo pipefail

environment="${1:?Usage: rollback-release.sh staging|production}"
[[ "${environment}" =~ ^(staging|production)$ ]]

state_dir="${DEPLOY_STATE_DIR:-./deploy/state}/${environment}"
state_dir="$(cd "${state_dir}" && pwd)"
previous_state="${state_dir}/previous.env"
test -f "${previous_state}"

set -a
source "${previous_state}"
set +a

[[ "${ENVIRONMENT}" == "${environment}" ]]
[[ "${COMMIT_SHA}" =~ ^[0-9a-f]{40}$ ]]
[[ "${RELEASE_DIR}" == /* ]]
test -d "${RELEASE_DIR}"
cd "${RELEASE_DIR}"

compose_files=(-f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.deploy.yml)
if [[ "${environment}" == "staging" ]]; then
  compose_files+=(-f docker-compose.staging.yml)
fi

if [[ "${DEPLOY_DRY_RUN:-0}" != "1" ]]; then
  docker compose --project-name "cybersentinel-${environment}" \
    "${compose_files[@]}" up -d --no-build --remove-orphans
  curl --fail --silent "${BASE_URL%/}/ready" >/dev/null
fi

cp "${previous_state}" "${state_dir}/current.env"
if [[ -n "${DEPLOY_CURRENT_LINK:-}" ]]; then
  ln -sfn "${RELEASE_DIR}" "${DEPLOY_CURRENT_LINK}"
fi
printf 'ROLLBACK_OK environment=%s commit=%s\n' "${environment}" "${COMMIT_SHA}"
