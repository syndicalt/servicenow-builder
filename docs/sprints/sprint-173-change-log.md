# Sprint 173 Change Log

## Scope

Production hardening: external alert delivery foundation.

## Changes

- Added `src/jedi_devproject/alert_delivery.py` as a standalone webhook delivery primitive.
- Added `ExternalAlert` with a strict schema for externally delivered alert payloads.
- Added `emit_alert_webhook()` with HTTPS URL enforcement, compact JSON payloads, oversized payloads rejected before send, and redacted delivery errors.
- Added runtime settings for future worker or scheduler wiring:
  - `JEDI_ALERT_WEBHOOK_ENABLED=false`
  - `JEDI_ALERT_WEBHOOK_URL`
  - `JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS=3`
  - `JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES=16384`
- Added production validation requiring HTTPS alert webhook URLs when external delivery is enabled.
- Documented that the worker does not automatically emit external alerts yet; this sprint creates the delivery primitive and configuration posture only.

## Verification

- `python3 -m pytest tests/test_alert_delivery.py -q` - 4 passed.
- `python3 -m pytest tests/test_runtime.py -k "alert_webhook or non_positive_runtime_limits" -q` - 4 passed, 75 deselected.
- `python3 -m pytest tests/test_project_docs.py -q` - 247 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1350 passed, 93.87% coverage.

## Residual Risk

- This sprint does not decide routing policy or automatically emit alerts from the worker. That should be a separate explicit integration slice so production incident behavior can be reviewed.
