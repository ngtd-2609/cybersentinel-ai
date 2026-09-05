# CyberSentinel incident runbook

## First response

1. Declare the incident, record UTC start time, environment, current commit and
   request IDs, then freeze non-reliability deployments.
2. Check `/health`, `/ready`, Prometheus targets, Grafana SLO panels and Loki logs.
3. Preserve logs and database evidence. Never copy credentials or raw secret files
   into tickets or chat.
4. If a new release correlates with the incident, run
   `scripts/rollback-release.sh <environment>` from the deployment state directory.
5. Confirm recovery with readiness, authentication/RBAC, ingestion and dashboard
   smoke tests. Record the recovery time and follow-up owner.

## API or service down

- Confirm host, container health, disk, memory and certificate expiry.
- Inspect `{service="api"}` and `{service="frontend"}` in Loki by request ID.
- Roll back if the failure began after deployment; otherwise restart only the
  unhealthy service and preserve its previous logs.

## High error rate

- Group 5xx by normalized route and request ID; check database and Redis health.
- Stop automated ingestion if it amplifies the failure, then drain queued work
  after recovery. Roll back a correlated release.

## High latency

- Compare P95 by normalized route with CPU, memory, PostgreSQL connection and query
  pressure. Check queue depth and downstream timeouts before scaling.
- Do not raise the SLO threshold to silence an alert.

## Database unavailable

- Confirm network/TLS/credential validity and managed-database status before any
  restart. Check storage and connection limits.
- Never restore over the primary during diagnosis. Restore the newest verified
  backup into a disposable database first, then follow the provider failover plan.

## Copilot timeout

- Confirm Ollama reachability and circuit state. The deterministic fallback keeps
  the analyst flow available and does not send data externally.
- Do not enable external or sensitive external AI as an incident workaround.

## Recovery and review

Close the incident only after 30 minutes of healthy SLO signals. Within two working
days document impact, timeline, root cause, detection gap, corrective actions and
whether the error-budget policy changes.
