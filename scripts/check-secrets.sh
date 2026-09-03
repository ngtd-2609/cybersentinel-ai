#!/usr/bin/env bash
set -euo pipefail

tracked_secrets="$(git ls-files | grep -E '(^|/)\.env$|\.(pem|key|p12|pfx)$' || true)"
if [[ -n "${tracked_secrets}" ]]; then
  printf 'Potential secret files are tracked:\n%s\n' "${tracked_secrets}" >&2
  exit 1
fi

if git grep -nE '(AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9_]{30,}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----)' -- ':!package-lock.json' ':!uv.lock'; then
  printf 'High-confidence credential pattern detected.\n' >&2
  exit 1
fi

printf 'No high-confidence tracked secrets detected.\n'
