#!/usr/bin/env bash
set -euo pipefail

environment="${1:?Usage: deploy-release.sh staging|production COMMIT_SHA BASE_URL}"
commit_sha="${2:?Usage: deploy-release.sh staging|production COMMIT_SHA BASE_URL}"
base_url="${3:?Usage: deploy-release.sh staging|production COMMIT_SHA BASE_URL}"

[[ "${environment}" =~ ^(staging|production)$ ]]
[[ "${commit_sha}" =~ ^[0-9a-f]{40}$ ]]
[[ "${base_url}" =~ ^https:// ]]

state_dir="${DEPLOY_STATE_DIR:-./deploy/state}/${environment}"
mkdir -p "${state_dir}"
state_dir="$(cd "${state_dir}" && pwd)"
if [[ -f "${state_dir}/current.env" ]]; then
  cp "${state_dir}/current.env" "${state_dir}/previous.env"
fi

api_image="${CYBERSENTINEL_API_IMAGE:-ghcr.io/ngtd-2609/cybersentinel-ai-api:${commit_sha}}"
frontend_image="${CYBERSENTINEL_FRONTEND_IMAGE:-ghcr.io/ngtd-2609/cybersentinel-ai-frontend:${commit_sha}}"
compose_files=(-f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.deploy.yml)
if [[ "${environment}" == "staging" ]]; then
  compose_files+=(-f docker-compose.staging.yml)
fi

export CYBERSENTINEL_API_IMAGE="${api_image}"
export CYBERSENTINEL_FRONTEND_IMAGE="${frontend_image}"

if [[ "${DEPLOY_DRY_RUN:-0}" != "1" ]]; then
  docker compose --project-name "cybersentinel-${environment}" \
    "${compose_files[@]}" pull
  docker compose --project-name "cybersentinel-${environment}" \
    "${compose_files[@]}" up -d --no-build --remove-orphans

  ready=0
  for _attempt in {1..60}; do
    if curl --fail --silent "${base_url%/}/ready" >/dev/null; then
      ready=1
      break
    fi
    sleep 2
  done
  if [[ "${ready}" != "1" ]]; then
    if [[ -f "${state_dir}/previous.env" ]]; then
      scripts/rollback-release.sh "${environment}"
    fi
    printf 'Deployment readiness failed; rollback attempted\n' >&2
    exit 1
  fi
fi

cat >"${state_dir}/current.env" <<EOF
ENVIRONMENT=${environment}
COMMIT_SHA=${commit_sha}
BASE_URL=${base_url}
RELEASE_DIR=${PWD}
CYBERSENTINEL_API_IMAGE=${api_image}
CYBERSENTINEL_FRONTEND_IMAGE=${frontend_image}
DEPLOYED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF

if [[ -n "${DEPLOY_CURRENT_LINK:-}" ]]; then
  ln -sfn "${PWD}" "${DEPLOY_CURRENT_LINK}"
fi

printf 'DEPLOYMENT_OK environment=%s commit=%s\n' "${environment}" "${commit_sha}"
