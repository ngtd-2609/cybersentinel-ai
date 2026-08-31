#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://127.0.0.1:8001}"
PROM_URL="${PROM_URL:-http://127.0.0.1:9091}"
GRAFANA_URL="${GRAFANA_URL:-http://127.0.0.1:3001}"

echo "=== CyberSentinel AI Final Demo Check ==="

echo
echo "[1/7] Docker services"
docker compose ps

echo
echo "[2/7] API health"
curl -fsS "${API_URL}/health"
echo

echo
echo "[3/7] Prometheus health"
curl -fsS "${PROM_URL}/-/healthy"
echo

echo
echo "[4/7] Prometheus target"

PROM_TARGET_UP=0

for attempt in $(seq 1 12); do
    TARGET_STATUS="$(
        curl -fsS "${PROM_URL}/api/v1/targets" | python3 -c '
import json, sys

data = json.load(sys.stdin)

for target in data["data"]["activeTargets"]:
    if target.get("labels", {}).get("job") == "cybersentinel-api":
        print(target.get("health", "unknown"))
        break
else:
    print("missing")
'
    )"

    if [ "${TARGET_STATUS}" = "up" ]; then
        PROM_TARGET_UP=1
        break
    fi

    echo "Waiting for Prometheus scrape... (${attempt}/12, status=${TARGET_STATUS})"
    sleep 5
done

if [ "${PROM_TARGET_UP}" -ne 1 ]; then
    echo "FAIL: Prometheus target did not become healthy"
    exit 1
fi

curl -fsS "${PROM_URL}/api/v1/targets" | python3 -c '
import json, sys

data = json.load(sys.stdin)

for target in data["data"]["activeTargets"]:
    if target.get("labels", {}).get("job") == "cybersentinel-api":
        print("job:", target["labels"].get("job"))
        print("health:", target.get("health"))
        print("error:", target.get("lastError", ""))
        break
'

echo
echo "[5/7] Grafana dashboard"
curl -fsS -u admin:admin \
  "${GRAFANA_URL}/api/dashboards/uid/cybersentinel-overview" | \
python3 -c '
import json, sys

data = json.load(sys.stdin)
dashboard = data.get("dashboard", {})

print("title:", dashboard.get("title"))
print("uid:", dashboard.get("uid"))

if dashboard.get("uid") != "cybersentinel-overview":
    raise SystemExit("FAIL: Grafana dashboard not found")
'

echo
echo "[6/7] SOC Copilot end-to-end"
curl -fsS --max-time 360 \
  -X POST "${API_URL}/copilot/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Give a short SOC response for this PortScan alert.",
    "alert_context": "Detected label: PortScan. Risk score: 78. Severity: HIGH.",
    "top_k": 4
  }' | python3 -c '
import json, sys

data = json.load(sys.stdin)

print("model:", data.get("model"))
print("sources:", len(data.get("sources", [])))

answer = data.get("answer", "").strip()
print("answer:", answer[:500])

if not answer:
    raise SystemExit("FAIL: Copilot returned an empty answer")
'

echo
echo "[7/7] Repository and DVC"
uv run dvc status
git status --short

echo
echo "=== FINAL DEMO CHECK: PASS ==="
