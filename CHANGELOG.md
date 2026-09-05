# Changelog

All notable changes are documented here. Versions follow Semantic Versioning.

## [Unreleased]

No unreleased changes.

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
