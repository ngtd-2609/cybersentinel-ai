#!/usr/bin/env bash
set -euo pipefail

state_root="$(mktemp -d)"
trap 'rm -rf "${state_root}"' EXIT
export DEPLOY_STATE_DIR="${state_root}"
export DEPLOY_DRY_RUN=1

scripts/deploy-release.sh staging aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa https://staging.example.test
scripts/deploy-release.sh staging bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb https://staging.example.test
scripts/rollback-release.sh staging

grep -q '^COMMIT_SHA=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa$' \
  "${state_root}/staging/current.env"
printf 'ROLLBACK_DRILL_OK\n'
