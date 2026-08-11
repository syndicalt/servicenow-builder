# Sprint 187 Change Log

Scope: Production hardening - alert webhook URL fragment rejection.

## Changes

- Extended `validate_alert_webhook_url()` to reject alert sink URLs containing URL fragments.
- Covered production startup validation for `JEDI_ALERT_WEBHOOK_URL` values with fragments.
- Preserved existing fail-closed validation for non-HTTPS URLs, embedded URL credentials, and sensitive query parameters.
- Documented that production alert webhook URLs must not include URL fragments because fragments are not sent to servers and can hide operator intent.

## Verification

- `python3 -m pytest tests/test_alert_webhook_url.py tests/test_runtime.py::test_validate_runtime_settings_rejects_alert_webhook_url_fragments tests/test_alert_delivery.py::test_emit_alert_webhook_rejects_non_https_url tests/test_alert_delivery.py::test_emit_alert_webhook_rejects_url_embedded_credentials -q` - 10 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 261 passed.
- `python3 -m mypy src tests` - passed; 171 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1396 passed, 93.91% coverage.
