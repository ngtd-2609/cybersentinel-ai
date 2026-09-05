#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repo_dir}"

if [[ "${PHASE_M_ALLOW_DIRTY:-false}" != "true" ]]; then
  test -z "$(git status --porcelain)"
fi
git diff --check

required_files=(
  README.md
  CHANGELOG.md
  CONTRIBUTING.md
  SECURITY.md
  docker-compose.demo.yml
  scripts/start-demo.sh
  scripts/stop-demo.sh
  docs/releases/v1.1.0.md
  docs/releases/v1.1.0-handoff.md
  docs/releases/v1.1.0-state.json
  docs/assets/dashboard.png
  docs/assets/incidents.png
  docs/assets/copilot.png
)
for required_file in "${required_files[@]}"; do
  test -s "${required_file}" || {
    printf 'Missing release artifact: %s\n' "${required_file}" >&2
    exit 1
  }
done

python3 -m json.tool docs/releases/v1.1.0-state.json >/dev/null
python3 - <<'PY'
import json
from pathlib import Path

state = json.loads(Path("docs/releases/v1.1.0-state.json").read_text())
required = {
    "clean_git_tree",
    "fresh_clone",
    "one_command_startup",
    "fresh_database_migration",
    "full_e2e",
    "security_scan",
    "backup_restore",
    "public_staging_smoke",
    "final_tag",
    "release_notes",
    "final_handoff",
    "state_json",
}
gates = {gate["id"]: gate["status"] for gate in state["gates"]}
missing = required - gates.keys()
if missing:
    raise SystemExit(f"Missing Phase M gates: {sorted(missing)}")
invalid = {name: status for name, status in gates.items() if status not in {"pass", "tag-time"}}
if invalid:
    raise SystemExit(f"Invalid Phase M gate states: {invalid}")
if state["release"]["version"] != "1.1.0":
    raise SystemExit("Release state must describe v1.1.0")
if state["video"]["status"] != "optional-deferred":
    raise SystemExit("The optional video must not block this release")
print("PHASE_M_STATE_OK")
PY

bash -n scripts/*.sh
bash scripts/check-secrets.sh

CYBERSENTINEL_SECRET_KEY=static-check-secret-key-at-least-32-characters \
CYBERSENTINEL_DEMO_USER_PASSWORD=static-check-demo-password \
CYBERSENTINEL_INGESTION_API_KEYS=static-check-ingestion-key \
docker compose --env-file .env.example \
  -f docker-compose.yml -f docker-compose.demo.yml config --quiet

test -z "$(git ls-files '.env' '.env.*' | grep -v '^.env.example$' || true)"
printf 'PHASE_M_STATIC_GATE_OK commit=%s\n' "$(git rev-parse HEAD)"
