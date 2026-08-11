# Sprint 828 Change Log - Alert webhook runtime construction guard

## Scope

Hardened runtime API construction so enabled alert webhook delivery cannot start with invalid outbound timeout or payload-size limits through direct `RuntimeSettings` paths.

## Tests First

- Added 1 failing-first alert webhook runtime construction assertion: `tests/test_runtime.py::test_create_runtime_api_rejects_invalid_alert_webhook_settings_before_store_open`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_828_documents_alert_webhook_runtime_construction_guard`.
- Initial failure proved invalid enabled-alert settings reached store construction before the runtime API rejected alert webhook timeout or body-size values.

## Changes

- Runtime API construction now rejects invalid enabled-alert `JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS` and `JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES` values with `RuntimeConfigError`.
- The construction guard rejects non-positive alert webhook timeouts, non-finite timeout values, timeout values above the production outbound ceiling, non-positive body-size limits, non-integer body-size values, and body-size limits above the production alert payload ceiling.
- Alert webhook settings are validated before alert transport creation, operational store opening, or route serving.
- Updated the operator guide to document that runtime API construction rejects invalid alert webhook settings in direct settings paths.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "invalid_alert_webhook_settings_before_store_open or runtime_rejected_event_emits_external_alert_without_enqueueing_worker"` - 7 passed, 386 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_828` - 1 passed, 900 deselected.
- `python3 -m pytest tests/test_runtime.py -q` - 393 passed.
- `python3 -m ruff check src tests` - All checks passed.
- `python3 -m mypy src tests` - Success: no issues found in 202 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 3273 passed, 93.37% coverage.
