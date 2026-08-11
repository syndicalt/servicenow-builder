# Sprint 307 Change Log - Alert Webhook URL Settings Load Guard

## Summary

- Runtime settings loading now validates configured `JEDI_ALERT_WEBHOOK_URL` values before settings are returned.
- Configured alert webhook URLs must be unpadded, free of control characters, HTTPS, credential-free, fragment-free, non-local, and free of sensitive query parameters.
- The guard applies even when `JEDI_ALERT_WEBHOOK_ENABLED=false`, so a dormant but unsafe alert sink configuration cannot sit silently in production env.
- Empty or absent `JEDI_ALERT_WEBHOOK_URL` values still behave as unconfigured, preserving the existing production requirement that enabled alert delivery must provide a URL.
- Malformed alert webhook URL diagnostics name only the setting and do not echo padded, control-character, or credential fragments.
- Existing delivery-time and production startup validation remains intact through the shared alert webhook URL validator.
- Added failing regressions proving padded, control-character, non-HTTPS, and credentialed `JEDI_ALERT_WEBHOOK_URL` env values were previously accepted during settings loading.
- Documented the alert webhook URL settings-load boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "malformed_alert_webhook_url or reads_alert_webhook_config or validate_runtime_settings_rejects_alert_webhook_url_credentials"` - 5 tests failed before implementation because malformed alert webhook URL values were accepted during settings loading.
- `python3 -m pytest tests/test_runtime.py -q -k "malformed_alert_webhook_url or reads_alert_webhook_config or validate_runtime_settings_rejects_alert_webhook_url_credentials"` - 7 passed after implementation.
- `python3 -m pytest tests/test_runtime.py -q` - 248 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_three_hundred_seven_documents_alert_webhook_url_load_guard -q` - 1 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 381 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1835 passed, total coverage 93.88%.
