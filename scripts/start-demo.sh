#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repo_dir}"

command -v docker >/dev/null || {
  printf 'Docker is required: https://docs.docker.com/get-docker/\n' >&2
  exit 2
}
docker compose version >/dev/null

env_file=".env.demo.local"
if [[ ! -f "${env_file}" ]]; then
  command -v openssl >/dev/null || {
    printf 'OpenSSL is required to generate local demo credentials.\n' >&2
    exit 2
  }
  umask 077
  demo_password="$(openssl rand -base64 24 | tr -d '\n')"
  secret_key="$(openssl rand -hex 32)"
  ingestion_key="$(openssl rand -hex 24)"
  {
    printf 'POSTGRES_USER=cybersentinel\n'
    printf 'POSTGRES_PASSWORD=%s\n' "$(openssl rand -hex 18)"
    printf 'POSTGRES_DB=cybersentinel\n'
    printf 'CYBERSENTINEL_SECRET_KEY=%s\n' "${secret_key}"
    printf 'CYBERSENTINEL_INGESTION_API_KEYS=%s\n' "${ingestion_key}"
    printf 'CYBERSENTINEL_DEMO_USER_PASSWORD=%s\n' "${demo_password}"
  } > "${env_file}"
  printf 'Created gitignored local demo credentials in %s (mode 600).\n' "${env_file}"
fi

compose=(docker compose --project-name cybersentinel-demo --env-file "${env_file}" \
  -f docker-compose.yml -f docker-compose.demo.yml)
"${compose[@]}" up -d --build

printf 'Waiting for the API and frontend to become ready...\n'
for attempt in $(seq 1 100); do
  api_ready=0
  web_ready=0
  curl --fail --silent http://127.0.0.1:8001/ready >/dev/null && api_ready=1 || true
  curl --fail --silent http://127.0.0.1:3002/login >/dev/null && web_ready=1 || true
  if [[ "${api_ready}" -eq 1 && "${web_ready}" -eq 1 ]]; then
    printf '\nCyberSentinel AI is ready.\n'
    printf '  Application: http://localhost:3002\n'
    printf '  API ready:   http://localhost:8001/ready\n'
    printf '  Prometheus:  http://localhost:9091\n'
    printf '  Grafana:     http://localhost:3001\n'
    printf 'Use the one-click safe demo account on the login page.\n'
    exit 0
  fi
  if (( attempt % 10 == 0 )); then
    printf 'Still starting (%s/100)...\n' "${attempt}"
  fi
  sleep 3
done

"${compose[@]}" ps
"${compose[@]}" logs --tail=80 api frontend
printf 'Startup timed out. Review the logs above.\n' >&2
exit 1
