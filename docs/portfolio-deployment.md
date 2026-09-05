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

1. Render Static Site for the frontend and managed HTTPS.
2. Render Free Web Service for the FastAPI application.
3. Neon Free PostgreSQL for durable demo data.
4. A free managed Redis service when required for distributed rate limiting and
   event delivery. Redis is never the authoritative store for demo data.
5. A portfolio runtime mode that performs bounded background work inside the web
   service when a free provider cannot run a separate worker. The normal external
   worker and Docker Compose paths remain supported.

Render Free Web Services can spin down after inactivity, and their local files are
ephemeral. Render Free PostgreSQL expires after 30 days, so it is not the default
database for this long-lived portfolio. Provider choices may be replaced with an
equivalent free or near-zero-cost combination if all gates below remain true.

Provider limits must be rechecked before account setup because free tiers can
change. Current references: [Render free services](https://render.com/docs/free)
and [Neon plans](https://neon.com/pricing).

## Required application work

- Add provider deployment manifests and documented build/start/migration commands.
- Configure the frontend API origin at build time and allow only the deployed
  frontend origin in backend CORS/CSP settings.
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
