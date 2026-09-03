# Production deployment

CyberSentinel uses the base Compose file for local development and
`docker-compose.prod.yml` for the production network boundary and TLS proxy.

## Required configuration

1. Copy `.env.example` to `.env` outside version control.
2. Replace every placeholder password and generate a unique JWT secret of at
   least 32 random characters.
3. Set `CYBERSENTINEL_HOSTNAME` to the public DNS name.
4. Place the TLS certificate and private key at
   `deploy/certs/fullchain.pem` and `deploy/certs/privkey.pem`. Never commit
   these files.

Validate configuration before starting:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml config --quiet
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

The production override exposes only Nginx on ports 80/443. PostgreSQL, API,
frontend, Prometheus and Grafana remain on the internal Compose network.

## Health and backup

- `/health` is the process liveness endpoint.
- `/ready` verifies that the API can query PostgreSQL.
- Run `scripts/backup-postgres.sh` from the repository root with
  `POSTGRES_USER` and `POSTGRES_DB` set.
- Test restores in a disposable database before relying on a backup.
- `scripts/restore-postgres.sh` requires both the SHA-256 sidecar and the
  explicit `CONFIRM_RESTORE=YES` guard.
