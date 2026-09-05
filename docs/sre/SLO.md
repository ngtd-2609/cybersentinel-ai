# Service level objectives

## Scope and measurement

The production API has a rolling 30-day availability objective of **99.5%**.
Availability is the ratio of non-5xx responses to all API responses. Planned
maintenance is included so deployment work consumes the same error budget as an
unexpected outage.

Normal API routes have a rolling 30-day **P95 latency objective below 500 ms**.
`/copilot/ask`, `/metrics`, streaming routes, and file exports are excluded from
the latency objective because their service behavior is intentionally different.

The monthly error budget is 0.5%, or approximately 3 hours 39 minutes in a
30-day month. Feature releases pause when both the 1-hour and 6-hour burn-rate
alerts fire. Reliability and security fixes may continue.

## Signals and alerts

- `cybersentinel:http_availability:ratio_5m` measures short-window availability.
- `cybersentinel:http_latency_p95_seconds:5m` measures P95 request latency.
- `cybersentinel_dependency_up{dependency="postgresql"}` reports database reachability.
- `cybersentinel_copilot_requests_total{outcome="fallback_unavailable"}` records
  local-model timeout, transport, retry exhaustion, and open-circuit fallback.

Prometheus evaluates the versioned rules in `monitoring/prometheus/rules`. Grafana
shows the SLO panels and centralized Loki logs in the CyberSentinel overview
dashboard. Every alert links to the incident runbook.

## Verification

Run `scripts/run-load-test.sh` against a warmed staging deployment. The k6 gate
fails when failed checks reach 0.5% or P95 latency reaches 500 ms. Record the run
URL, timestamp, commit, traffic profile, and result in the Phase L evidence file.
