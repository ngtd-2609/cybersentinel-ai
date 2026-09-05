# Public portfolio deployment

## Objective

CyberSentinel AI is deployed as a public, interactive portfolio project rather
than a commercial production service. A reviewer must be able to open one HTTPS
URL and exercise the main product without installing code or Docker. The frontend,
API and PostgreSQL database are real hosted components; the developer laptop is
not part of the runtime path.

Free-tier cold starts and modest quotas are acceptable when they are documented
and the UI explains that the demo may need time to wake up. A custom domain, VPS,
Kubernetes, Kafka and a self-hosted observability stack are optional.

## Preferred low-cost architecture

The initial baseline is:

1. Render Free Web Service for the Next.js frontend/BFF and managed HTTPS.
2. Render Free Web Service for the FastAPI application.
3. Neon Free PostgreSQL for durable demo data.
4. A free managed Redis service when required for distributed rate limiting and
   event delivery. Redis is never the authoritative store for demo data.
5. A portfolio runtime mode that performs bounded background work inside the API
   service when a free provider cannot run a separate worker. The normal external
   worker and Docker Compose paths remain supported.

The frontend remains a web service rather than a static export because it owns the
HTTP-only session cookies, server-side API proxy and authenticated SSE bridge.

Render Free Web Services can spin down after inactivity, and their local files are
ephemeral. Render Free PostgreSQL expires after 30 days, so it is not the default
database for this long-lived portfolio. Provider choices may be replaced with an
equivalent free or near-zero-cost combination if all gates below remain true.

Provider limits must be rechecked before account setup because free tiers can
change. Current references: [Render free services](https://render.com/docs/free)
and [Neon plans](https://neon.com/pricing).

## What is already automated

The root `render.yaml` creates both Render services from `main`, waits for GitHub
checks before automatic deployments, generates the application signing key and
ingestion API key, wires the public API URL into the frontend, restricts backend
CORS to the frontend URL, runs database migrations, seeds the safe demo dataset,
and starts the bounded ingestion worker inside the API process.

The same demo password is passed from the API service to the frontend through a
Render service reference. It is entered once and is never stored in Git or baked
into the frontend image.

## First public deployment

### 1. Create the Neon database

1. Sign in to Neon and create a project in a region near Singapore when available.
2. Keep the default PostgreSQL database and role; no table creation is needed.
3. Open **Connect**, select the pooled connection and copy its connection string.
4. Ensure the URL begins with `postgresql://` or `postgres://` and includes
   `sslmode=require`. Treat the complete URL as a secret.

Alembic creates the schema automatically during the API's first startup. Do not
paste this URL into GitHub, a tracked `.env`, an issue, or a screenshot.

### 2. Choose the only user-managed application secret

Generate a unique demo password locally with a password manager or a cryptographic
password generator. Use at least 24 random characters. Do not reuse a personal,
GitHub, email, database or administrator password.

### 3. Apply the Render Blueprint

1. Sign in to Render with the GitHub account that can read this repository.
2. Choose **New +** then **Blueprint**, select `ngtd-2609/cybersentinel-ai`, and
   keep `render.yaml` as the Blueprint path.
3. Review that the plan for both services is **Free** and the region is Singapore.
4. Render prompts for exactly these `sync: false` values:
   - `CYBERSENTINEL_DATABASE_URL`: paste the Neon connection string.
   - `CYBERSENTINEL_DEMO_USER_PASSWORD`: paste the new demo password.
5. Apply the Blueprint. Never enter the demo password into the frontend service;
   the Blueprint references the API value automatically.

The first API deploy runs `alembic upgrade head`, creates the restricted `ANALYST`
demo account, and inserts synthetic RFC 5737 security data. Repeated deploys are
idempotent and do not duplicate the dataset.

### 4. Verify the deployment

Wait for both services to show **Live**, then check:

1. Open `https://<api-service>.onrender.com/ready`; expect HTTP 200 and a ready
   response. `/docs` and `/redoc` must return 404 in portfolio mode.
2. Open `https://<web-service>.onrender.com/login`. The wake-up notice may remain
   for about a minute after 15 minutes of inactivity.
3. Click **Explore with the safe demo account**. No credential should be visible
   in page source, browser storage or the Git repository.
4. Exercise Dashboard, Events, Incidents, Threat Intel, Copilot and Reports.
5. In Render, confirm both services show the same deployed Git commit and no
   secret value appears in build or application logs.

Record the final web URL and the successful smoke evidence in the Phase L handoff.
Do not create the final release tag until the Phase M Final Release Gate passes.

## Reseed and recovery

Normal redeploys preserve viewer changes. To restore canonical demo state, use a
temporary Render Shell only if the selected plan supports it, or run the following
command from a trusted machine with the Neon URL and demo password supplied only
through environment variables:

```bash
python -m cybersentinel_ai.demo.seed --reset
```

The reset restores the restricted role and canonical incidents, rotates the demo
password to the configured value, and revokes existing demo sessions. If a free
plan offers no shell, temporarily set a one-time reset command on the API service,
deploy it, verify `DEMO_SEED_OK ... reset=true`, then immediately restore the normal
Docker command. Never place the secret values in that command.

## Cost and availability notes

- Two Render Free Web Services share the workspace's 750 monthly free instance
  hours. Because sleeping services do not consume hours, this is suitable for an
  occasional portfolio demo but not continuous production traffic.
- Each service can sleep after 15 idle minutes and needs about a minute to wake.
- The service filesystem is ephemeral; PostgreSQL is the authoritative state.
- Neon Free quotas and Render Free limits can change. Recheck provider dashboards
  before a public CV campaign and set spend limits or avoid adding a payment method
  if unexpected billing must be impossible.

## Required application work

- Add provider deployment manifests and documented build/start/migration commands.
- Wire the frontend API origin and deployed frontend CORS origin from Render
  service properties rather than committing environment-specific URLs.
- Make migrations safe and repeatable against an empty managed PostgreSQL database.
- Add an idempotent demo seed/reseed command with synthetic events, incidents,
  threat intelligence, Copilot context and report data.
- Provide a restricted, non-admin demo account. Keep public registration disabled
  and never reuse any developer or administrative credential.
- Keep every provider token, database URL, application key and demo password in
  provider secret settings. Commit only names and examples.
- Use the existing grounded Copilot fallback when no hosted model is configured,
  and label fallback responses honestly in the demo UI.
- Add a wake-up/loading state for backend cold starts and retry health checks with
  a bounded timeout.
- Add a public Playwright smoke that covers Login, Dashboard, Events, Incidents,
  Threat Intel, Copilot and Reports.

## Definition of Done

- A public provider URL serves HTTPS without certificate warnings.
- A new visitor needs only a browser and documented demo credentials.
- The API and managed PostgreSQL persist data independently of the developer laptop.
- Seed/reseed is idempotent, synthetic and safe; the demo account cannot administer
  real users or secrets.
- Health/readiness, main demo journey, migration, security scan and public smoke
  pass on the recorded release candidate.
- The README states provider limitations, especially cold start and quota behavior.
- No password, token, private key, production `.env` or database URL is tracked.

## Optional advanced evidence

The existing Compose/Caddy staging deployment, immutable GHCR images, Grafana,
Prometheus, Loki, k6 SLO, systemd backup timers and rollback workflows remain
valuable SRE evidence. They may be demonstrated locally or on a temporary host,
but a paid VPS and a permanent production-like staging environment are not release
blockers for this portfolio target.
