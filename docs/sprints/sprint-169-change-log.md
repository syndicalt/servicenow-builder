# Sprint 169 Change Log

## Scope

Production hardening: operational alert projection for failed and rejected fulfillment jobs.

## Changes

- Added authenticated `GET /admin/alerts` to expose Operational Alerts for operator diagnostics.
- Kept alerts as a read-only projection over recent fulfillment jobs instead of adding a separate mutable alert queue.
- Included `job_id`, `event_id`, story number, `correlation_id`, status, attempt count, updated timestamp, severity, summary, redacted detail, and operator action in each alert.
- Rendered Operational Alerts in the read-only admin console.
- Reused runtime diagnostic redaction so alert details do not leak ServiceNow URL credentials, token query parameters, database URLs, or other sensitive diagnostic values.
- Documented the alert contract in `docs/operator-guide.md`, including the intended drill-down path from alert to `/jobs/{job_id}/events` and ServiceNow work notes.

## Verification

- `python3 -m pytest tests/test_runtime.py -k "admin_alerts or admin_console_renders_operational_alerts" -q` - 4 passed, 68 deselected.
- `python3 -m pytest tests/test_runtime.py -q` - 72 passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 240 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1325 passed, 93.79% coverage.

## Residual Risk

- This sprint does not implement external alert delivery to email, Teams, PagerDuty, or ServiceNow incidents. It creates the sanitized operator-facing projection that those emitters can consume later.
- Stale running-job detection is not included yet. The current projection focuses on terminal attention states that already have durable runtime status.
