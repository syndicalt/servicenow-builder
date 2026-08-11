# Sprint 181 Change Log

## Scope

Production hardening: alert webhook response diagnostic redaction.

## Changes

- Hardened `emit_alert_webhook()` failure messages so alert sink response bodies are recursively redacted before being included in `AlertDeliveryError`.
- Preserved structured key redaction for fields such as `access_token` and `client_secret`.
- Added diagnostic string redaction inside response payloads, including plain assignments such as `client_secret=value`, URL passwords, and sensitive query parameters.
- Kept successful alert delivery behavior unchanged.
- Documented the response redaction boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_alert_delivery.py -q` - 13 passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 255 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1379 passed, 93.88% coverage.

## Residual Risk

- Response redaction is defensive diagnostic hygiene. Alert receivers should still avoid returning secrets in error responses.
