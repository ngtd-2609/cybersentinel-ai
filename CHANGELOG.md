# Changelog

All notable changes are documented here. Versions follow Semantic Versioning.

## [Unreleased]

### Added

- Staging and immutable-image deployment configuration with automatic HTTPS.
- Docker secret-file configuration sourced from GitHub Environment secrets.
- Loki/Promtail centralized logs and expanded Grafana SLO dashboard.
- Availability, latency, database and Copilot alert rules.
- Automated PostgreSQL backup/restore drill, k6 SLO test and deployment rollback.
- SLO policy, incident runbook and Phase L evidence ledger.

Release tagging remains blocked until the HTTPS staging, restore, load and rollback
gates pass on the exact release commit.
