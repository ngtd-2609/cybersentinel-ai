# Security Policy

CyberSentinel AI is a defensive research and portfolio project. It is not a
managed security product and does not provide a production support SLA.

## Reporting a vulnerability

Please do not open a public issue for a vulnerability that could expose user
sessions, credentials, provider configuration, or the public demo database.
Instead, use GitHub's **Report a vulnerability** private advisory flow for
`ngtd-2609/cybersentinel-ai`. Include:

- the affected commit, route, or component;
- reproduction steps using synthetic data;
- expected and observed impact;
- a minimal proof of concept with all secrets removed;
- a suggested mitigation, if available.

Do not test denial of service, credential attacks, destructive payloads, or data
exfiltration against the public Render/Neon deployment. Reproduce safely in your
own local environment.

## Supported version

Security fixes target the latest GitHub release and the current `main` branch.
Older tags are retained for provenance but are not maintained as separate support
lines.

## Secrets and data

Never commit or submit real credentials, private keys, database URLs, personal
data, production telemetry, or unauthorized network captures. Use the synthetic
demo dataset and RFC 5737 documentation addresses in reports and tests.

## Security controls

The release pipeline includes secret hygiene, dependency auditing, Bandit SAST,
Trivy container scanning, Redis quota integration, PostgreSQL backup/restore, and
OWASP ZAP API scanning. Passing these controls reduces risk but is not a security
guarantee.
