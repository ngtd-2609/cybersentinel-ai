#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repo_dir}"

env_file=".env.demo.local"
if [[ ! -f "${env_file}" ]]; then
  printf 'No %s file exists; using .env.example only for Compose interpolation.\n' "${env_file}"
  env_file=".env.example"
fi

compose=(docker compose --project-name cybersentinel-demo --env-file "${env_file}" \
  -f docker-compose.yml -f docker-compose.demo.yml)
if [[ "${1:-}" == "--volumes" ]]; then
  "${compose[@]}" down --volumes
else
  "${compose[@]}" down
fi
