#!/usr/bin/env bash
set -euo pipefail

base_url="${STAGING_URL:?Set STAGING_URL to the HTTPS staging origin}"
if [[ ! "${base_url}" =~ ^https:// ]]; then
  printf 'STAGING_URL must use HTTPS\n' >&2
  exit 2
fi
staging_host="${base_url#https://}"
staging_host="${staging_host%/}"
[[ "${staging_host}" != */* ]]

curl --fail --silent --show-error --proto '=https' --tlsv1.2 \
  "${base_url%/}/health" | grep -q '"status":"ok"'
curl --fail --silent --show-error --proto '=https' --tlsv1.2 \
  "${base_url%/}/ready" | grep -q '"status":"ready"'

certificate_end="$(echo | openssl s_client -servername "${staging_host}" \
  -connect "${staging_host}:443" 2>/dev/null \
  | openssl x509 -noout -enddate)"
test -n "${certificate_end}"

printf 'STAGING_HTTPS_SMOKE_OK url=%s %s\n' "${base_url}" "${certificate_end}"
