# Production deployment

CyberSentinel uses the base Compose file for local development and
`docker-compose.prod.yml` for the production network boundary and TLS proxy.

## Required configuration

1. Create a GitHub `staging` Environment and configure the variables and secrets
   listed below. Do not put deployment secrets in `.env`.
2. Set `CYBERSENTINEL_HOSTNAME` to the public DNS name.
3. For manual production TLS, place the TLS certificate and private key at
   `deploy/certs/fullchain.pem` and `deploy/certs/privkey.pem`. Never commit
   these files.

Validate configuration before starting:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml config --quiet
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

The production override exposes only Nginx on ports 80/443. PostgreSQL, API,
frontend, Prometheus and Grafana remain on the internal Compose network.

Staging uses `docker-compose.staging.yml` and Caddy ACME automation. Point the
staging hostname's A/AAAA record at the staging host and allow inbound TCP 80/443.
The staging and production Compose project names must differ so networks, volumes
and databases cannot collide.

## GitHub staging environment

Variables: `STAGING_HOSTNAME`, `ACME_EMAIL`.

Secrets: `STAGING_SSH_HOST`, `STAGING_SSH_USER`, `STAGING_SSH_PRIVATE_KEY`,
`STAGING_POSTGRES_PASSWORD`, `STAGING_DATABASE_URL`, `STAGING_APP_SECRET_KEY`,
`STAGING_INGESTION_API_KEYS`, `STAGING_GRAFANA_ADMIN_PASSWORD`,
`GHCR_PULL_USERNAME`, and a read-packages `GHCR_PULL_TOKEN`.

The manual **Deploy staging** workflow builds commit-SHA-tagged images, transfers
the exact release source, materializes GitHub Environment secrets as mode-600
Docker secret files, deploys, checks readiness and verifies public HTTPS. Protect
the environment with required reviewers before using it for production-like data.

After deployment, run the manual **Operate staging** workflow. The `status`
operation lists the Compose services and checks HTTPS, `verify` additionally runs
the k6 SLO gate and disposable backup/restore drill, and `rollback` restores the
recorded previous release and verifies HTTPS. These operations consume the same
GitHub `staging` Environment credentials, so operators never need to copy the SSH
private key out of GitHub.

## Release and rollback

`scripts/deploy-release.sh` records the current and previous immutable image tags.
If readiness fails, it automatically invokes the previous release. Operators can
run `scripts/rollback-release.sh staging` from the release directory with
`DEPLOY_STATE_DIR=/opt/cybersentinel/staging/state` for manual rollback. Follow the
incident runbook and record the drill in `docs/sre/phase-l-evidence.md`.

After every Phase L gate passes on the same commit, create the release candidate
with `scripts/tag-release.sh v0.2.0-rc.1`, review the annotated tag, and push it.
Final product tagging remains part of the Phase M Final Release Gate.

## Health and backup

- `/health` is the process liveness endpoint.
- `/ready` verifies that the API can query PostgreSQL.
- Run `scripts/backup-postgres.sh` from the repository root with
  `POSTGRES_USER` and `POSTGRES_DB` set.
- Run `scripts/backup-restore-drill.sh` on a schedule and before release. It
  restores into a disposable database and verifies migration head/table count.
- `scripts/restore-postgres.sh` requires both the SHA-256 sidecar and the
  explicit `CONFIRM_RESTORE=YES` guard.
- Keep encrypted backups outside the deployment host. Target RPO is 24 hours and
  target RTO is 60 minutes; retain daily backups for 7 days and monthly backups
  for 3 months.
- Install the versioned `deploy/systemd` units for daily backups and weekly
  disposable restore drills. `/etc/cybersentinel/<environment>-backup.env` must
  contain `POSTGRES_USER`, `POSTGRES_DB`, `BACKUP_DIR`,
  `COMPOSE_PROJECT_NAME=cybersentinel-<environment>` and the four-file
  `COMPOSE_FILE` chain. Enable `cybersentinel-backup@<environment>.timer` and
  `cybersentinel-restore-drill@<environment>.timer` only after the service account
  has write access to the encrypted backup destination and scoped Docker access.

## Observability and load

Promtail centralizes Docker logs in Loki. Grafana provisions both Prometheus and
Loki data sources and the SLO dashboard. Alert rules cover API down, 5xx/error
budget, P95 latency, PostgreSQL availability and Copilot fallback bursts.

Run `BASE_URL=https://<staging-host> scripts/run-load-test.sh` after warming the
deployment. The k6 gate enforces availability above 99.5% and P95 below 500 ms.
