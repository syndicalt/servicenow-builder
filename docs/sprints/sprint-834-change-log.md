# Sprint 834 Change Log - Alert webhook direct body-limit guard

## Intent

Harden the direct alert webhook delivery primitive so embedded callers cannot
pass malformed body-size controls that bypass environment parsing or fail after
other outbound validation work has already started.

## Changes

- Added 1 failing-first alert webhook body-limit assertion: `tests/test_alert_delivery.py::test_emit_alert_webhook_rejects_invalid_max_body_bytes_before_url_validation`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_834_documents_alert_webhook_direct_body_limit_guard`.
- `emit_alert_webhook()` now validates direct `JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES` shaped values before URL validation, alert serialization, or transport use.
- Invalid direct body limits fail with `alert webhook max body bytes must be a positive integer`.

## Verification

- `pytest tests/test_alert_delivery.py::test_emit_alert_webhook_rejects_invalid_max_body_bytes_before_url_validation tests/test_alert_delivery.py::test_emit_alert_webhook_sends_bounded_json_payload tests/test_project_docs.py::test_sprint_834_documents_alert_webhook_direct_body_limit_guard -q` - 6 passed.
- `pytest tests/test_alert_delivery.py -q` - 75 passed.
- `pytest tests/test_project_docs.py -q` - 907 passed.
- `pytest --cov=src/jedi_devproject --cov-report=term-missing -q` - 3324 passed, 93.42% coverage.
