# Phase L public portfolio verification evidence

This file is updated only with evidence from the exact deployed commit.

## Required public portfolio gates

| Gate | Result | Evidence |
| --- | --- | --- |
| Public HTTPS URL | PENDING | Provider deployment not created yet |
| Hosted frontend and API | PENDING | Must work without Docker on the viewer's machine |
| Managed PostgreSQL and migration | PENDING | Empty hosted database must migrate to Alembic head |
| Safe demo seed and restricted account | PENDING | Idempotent seed/reseed and non-admin demo access required |
| Main demo journey | PENDING | Login, Dashboard, Events, Incidents, Threat Intel, Copilot and Reports |
| Laptop independence | PENDING | Public deployment must remain available when the developer laptop is off |
| Secret hygiene | PASS | CI scans tracked files; provider values must remain outside Git |
| Cold-start UX | PENDING | Free-tier wake-up behavior must be tested and documented |

Phase L remains open until every required public portfolio row records a UTC
timestamp, commit/deployment ID and successful run or public URL evidence.

## Advanced self-hosted SRE evidence (non-blocking)

| Gate | Result | Evidence |
| --- | --- | --- |
| Separate staging configuration | PASS | `docker-compose.staging.yml` with isolated Compose project/volumes |
| Secret-manager flow | PASS | GitHub Environment secrets materialized as mode-600 Docker secret files |
| Centralized logs | PASS | Promtail to Loki; Loki datasource and logs panel provisioned in Grafana |
| SLO and alerts | PASS | Versioned recording/alert rules and Grafana SLO dashboard |
| Backup/restore automation | IMPLEMENTED | `scripts/backup-restore-drill.sh`; runtime result pending exact Phase L commit |
| Load gate | IMPLEMENTED | k6 99.5%/500 ms thresholds; staging result pending |
| Rollback | IMPLEMENTED | immutable image state and automatic/manual rollback; staging drill pending |
| HTTPS self-hosted URL | OPTIONAL | No VPS/DNS/SSH credentials required for portfolio Definition of Done |

## Local preflight — 2026-09-05 UTC

- Secret-file, observability and route-cardinality tests: 18 passed.
- Backup/restore script: pass against the local PostgreSQL service; disposable
  database matched migration `f2b9c7d1a450` and 13 public tables, then was removed.
- k6 warm smoke: 442/442 checks, 0% failed requests, P95 28.26 ms with 5 VUs for
  10 seconds. This is preflight only and does not replace the staging SLO run.
- Rollback dry-run: deployed synthetic revision B, restored revision A, and verified
  the current state pointer.
- Prometheus `promtool`: 7 rules valid. Loki and Promtail config validators: pass.
- Docker Compose merge, Grafana JSON, GitHub workflow actionlint, Ruff and shell
  syntax checks: pass.
