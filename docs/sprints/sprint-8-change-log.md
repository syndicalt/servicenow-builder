# Sprint 8 Change Log

## Scope

Sprint 8 added the read-only ServiceNow PDI integration foundation using OAuth client credentials while keeping normal tests offline and fixture-backed.

## Changes

- OAuth client credentials auth path in `src/jedi_devproject/servicenow.py`.
- Read-only Table API client for `rm_story` ingestion.
- Transport protocol boundary so tests use fake responses instead of live PDI calls.
- `UrllibTransport` for real HTTP calls when explicitly wired by a developer.
- `.env` parser for local OAuth credentials without adding a dotenv dependency.
- `SERVICENOW_INSTANCE_URL`, `SERVICENOW_CLIENT_ID`, and `SERVICENOW_CLIENT_SECRET` are the required local `.env` keys.
- `.env.example` documents the required local key names without containing secrets.
- `.env` added to `.gitignore`.
- Secret redaction for authorization headers, client secrets, access tokens, refresh tokens, and passwords.
- API failure handling through `ServiceNowApiError`.
- ServiceNow record mapping into validated `Story` models.
- No live PDI calls in default tests.

## Assumptions Challenged

- OAuth client credentials is the default development path because this project is service-style and should not depend on an interactive browser user.
- Basic auth remains intentionally absent from the core client. Adding it later would require a separate dev-only adapter and tests proving it is disabled by default.
- Live PDI tests are not part of the default gate because repeatable CI-quality tests must not depend on external instance availability or local credentials.

## Verification Evidence

Target command:

```bash
python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest --cov=jedi_devproject --cov-report=term-missing --cov-fail-under=90
```

Expected result:

- Ruff passes.
- Mypy passes.
- Pytest passes.
- Coverage remains above the 90% gate.

The change log itself is covered by `tests/test_project_docs.py`.

## Live PDI Smoke Test

After `SERVICENOW_INSTANCE_URL`, `SERVICENOW_CLIENT_ID`, and `SERVICENOW_CLIENT_SECRET` were present in local `.env`, a manual smoke test was run against the PDI:

- OAuth token request completed successfully.
- Read-only `GET /api/now/table/rm_story` completed with HTTP 200.
- Query used `sysparm_limit=1`.
- One `rm_story` record was returned.
- No token, client secret, or record identifiers were printed in the final user-facing summary.
