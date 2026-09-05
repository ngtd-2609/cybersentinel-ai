# Contributing to CyberSentinel AI

CyberSentinel AI is primarily a portfolio and defensive research project. Small,
well-scoped fixes and reproducible improvements are welcome.

## Before opening a change

1. Use only data and systems you are authorized to test.
2. Open a normal issue for bugs or feature discussion; use the private process in
   `SECURITY.md` for vulnerabilities.
3. Keep the public demo safe: no real telemetry, credentials, exploit payloads, or
   destructive actions.
4. Preserve the official implementation order and do not rewrite completed phase
   history unless fixing a documented regression.

## Development workflow

```bash
git clone https://github.com/ngtd-2609/cybersentinel-ai.git
cd cybersentinel-ai
uv sync --locked --dev
cd frontend && npm ci && cd ..
uv run pre-commit install
```

Before submitting a pull request:

```bash
uv run ruff check .
uv run pytest
uv run python -m cybersentinel_ai.evaluation.phase_k --check
cd frontend && npm run lint && npm run build && npm run test:e2e
```

Changes to schema, authentication, ingestion, release scripts, or provider
configuration should include tests and a brief threat/rollback note in the pull
request.

## Pull request checklist

- the change is focused and explained;
- tests cover the intended behavior and important failure cases;
- no secret, private key, database URL, or personal data is included;
- migrations upgrade from an empty PostgreSQL database;
- user-facing or operational behavior is documented;
- generated artifacts are intentional and reproducible.

By contributing, you confirm that you have the right to submit the change. No
open-source license is currently declared, so contribution acceptance does not by
itself grant broad reuse rights.
