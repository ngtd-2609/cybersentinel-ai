# Changelog

## [Unreleased]

No unreleased changes.

## [1.2.0] - 2026-09-06

- Added private, expiring per-user simulation sandboxes with five safe attack scenarios.
- Added user-visible event creation, automatic sandbox incidents, reset controls, server search and pagination.
- Added one-time Owner Admin bootstrap, reserved owner identity and Admin-managed account creation.
- Added account password changes, data-backed notifications and live API health status.
- Isolated Events, Incidents and Dashboard data by workspace and user while preserving read-only demo evidence.
- Added persisted asset context, incident-to-asset and incident-to-detection relationships.
- Expanded incidents into cases with display IDs, priorities, assignees, tags, resolution metadata and combined filters.
- Added cached AbuseIPDB IP reputation behind an optional server-only API key with graceful fallback.
- Added persisted, auditable simulated containment actions for public sandbox investigations.
- Reworked the seed into one coherent six-detection attack chain and added Vercel frontend deployment metadata.

All notable changes are documented here. Versions follow Semantic Versioning.

## [1.1.1] - 2026-09-06

### Added

- Safe public self-registration with automatic sign-in, Viewer-only access,
  per-IP throttling, and a bounded account capacity.
- Persistent English/Vietnamese interface control and a functional settings page.
- Mobile navigation drawer, global event search, and notification status panel.

### Fixed

- Replaced inert dashboard controls with real routes and corrected incident links
  to use database identifiers.
- Replaced simulated dashboard/model-health claims with live API data or honest
  configured-state labels.
- Reset the shared portfolio seed to its canonical incidents and restricted the
  one-click demo account to Viewer access.
- Added E2E coverage for registration, mobile navigation, language switching,
  notifications, incident navigation, and Copilot entry points.

## [1.1.0] - 2026-09-05

### Added

- Public Render + Neon portfolio deployment with restricted one-click demo data.
- Complete Next.js SOC workspace, secure BFF sessions, incidents, threat context,
  Copilot, reports, model monitoring, and administrative controls.
- Real-time ingestion/incident operations and AI reliability/MLOps lifecycle.
- Staging and immutable-image deployment configuration with automatic HTTPS.
- Docker secret-file configuration sourced from GitHub Environment secrets.
- Loki/Promtail centralized logs and expanded Grafana SLO dashboard.
- Availability, latency, database and Copilot alert rules.
- Automated PostgreSQL backup/restore drill, k6 SLO test and deployment rollback.
- SLO policy, incident runbook and Phase L evidence ledger.
- One-command local demo, GitHub-focused README, screenshots, security and
  contribution policies, release notes, final handoff, and release state JSON.

### Security

- Added session rotation/replay handling, RBAC, administrator MFA, account
  lockout, rate limiting, hardened portfolio headers, audit context, secret
  hygiene, dependency/SAST/container/DAST scans, and backup/restore verification.

### Notes

- The optional 5–8 minute demo video is deferred and does not block v1.1.0.
