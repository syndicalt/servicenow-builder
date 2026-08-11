# Sprint 168 Change Log

## Scope

Deployment health readiness hardening. This sprint adds a sanitized readiness probe so a
production host can distinguish process liveness from operational-store readiness before
routing ServiceNow lifecycle traffic or operator diagnostics to the runtime.

## Changes

- Added unauthenticated `GET /ready` to the runtime API wrapper.
- `GET /ready` performs a minimal read-only operational-store query with
  `recent_lifecycle_events(limit=1)`.
- Successful readiness returns `200` with `status=ready` and an `operational_store` check.
- Failed readiness returns `503` with `status=unready` and a failed `operational_store` check.
- Readiness failures do not return exception text, database URLs, credentials, or other
  diagnostic secrets.
- Updated `docs/operator-guide.md` to document `GET /health` as liveness and `GET /ready` as
  dependency readiness.

## Verification

- Focused red/green tests:
  `python3 -m pytest tests/test_runtime.py -k "runtime_readiness_checks_operational_store_without_auth or runtime_readiness_fails_closed_without_secret_leakage" -q`
  — 2 passed after implementation.
- Runtime regression:
  `python3 -m pytest tests/test_runtime.py -q`
  — 68 passed.
- Full quality gate:
  `python3 -m ruff check src tests`
  — passed.
- Full type gate:
  `python3 -m mypy src tests`
  — passed.
- Full coverage gate:
  `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`
  — 1319 passed, 93.79% coverage.

## Notes

- The readiness probe is intentionally small and read-only. It does not expose lifecycle
  payloads, job records, artifact data, ServiceNow sys_ids, or exception details.
- This is an application readiness signal. Hosts should still wire external health checks,
  alerting, restart policy, and edge monitoring according to the target Federal deployment
  environment.
