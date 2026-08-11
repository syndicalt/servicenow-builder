# Sprint 178 Change Log

## Scope

Production hardening: alert webhook header injection defense.

## Changes

- Added pre-send validation for alert webhook metadata header values.
- Rejected generated `alert_id`, `job_id`, `event_id`, story number, or correlation id values that contain ASCII control characters.
- Alert delivery now fails before transport invocation when unsafe header values are present.
- Kept the JSON payload unchanged. This sprint only hardens the outbound HTTP metadata boundary.
- Documented the header validation invariant in the operator guide.

## Verification

- `python3 -m pytest tests/test_alert_delivery.py -q` - 13 passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 252 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1374 passed, 93.89% coverage.

## Residual Risk

- Alert retry/backoff remains caller or host owned. This sprint only protects the outbound header construction boundary.
