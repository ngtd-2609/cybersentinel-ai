#!/usr/bin/env bash
set -euo pipefail

base_url="${BASE_URL:-http://127.0.0.1:8001}"

docker run --rm --network host \
  -e BASE_URL="${base_url}" \
  -e SLO_VUS="${SLO_VUS:-10}" \
  -e SLO_DURATION="${SLO_DURATION:-30s}" \
  -e HOST_HEADER="${HOST_HEADER:-}" \
  -v "${PWD}/load/k6:/scripts:ro" \
  grafana/k6:1.2.3 run /scripts/slo.js
