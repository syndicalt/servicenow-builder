# Sprint 177 Change Log

## Scope

Production hardening: outbound alert webhook idempotency and correlation headers.

## Changes

- Added stable metadata headers to every external alert webhook request:
  - `Idempotency-Key`
  - `X-JEDI-Alert-ID`
  - `X-JEDI-Job-ID`
  - `X-JEDI-Event-ID`
  - `X-JEDI-Story-Number`
  - `X-JEDI-Correlation-ID`, only when the alert has a correlation id
- Kept alert JSON payloads unchanged so existing receivers can continue parsing the body.
- Documented that downstream alert receivers should treat `Idempotency-Key` as the dedupe key for retry-safe incident creation.

## Verification

- `python3 -m pytest tests/test_alert_delivery.py -q` - 8 passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 251 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1368 passed, 93.89% coverage.

## Residual Risk

- Alert retry policy is still caller/host owned. The webhook primitive now provides a stable dedupe key, but it does not perform retries internally.
