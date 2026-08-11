# Sprint 252 Change Log - Runtime Numeric Parsing Hygiene

## Summary

- Runtime numeric parsing hygiene prevents malformed numeric environment values from surfacing raw parser errors or losing the setting name.
- Added parameterized runtime settings regression tests for malformed integer values across request body limits, rate limits, stale-job thresholds, HSTS max age, alert webhook body size, and public-web byte/result limits.
- Added parameterized runtime settings regression tests for malformed timeout values across `JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS` and `JEDI_PUBLIC_WEB_TIMEOUT_SECONDS`.
- Updated `load_runtime_settings()` numeric parsers so malformed values raise `RuntimeConfigError` with the setting name and expected numeric type.
- Documented that malformed runtime numeric values fail settings loading with stable, setting-specific diagnostics.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_load_runtime_settings_rejects_malformed_runtime_integer_values tests/test_runtime.py::test_load_runtime_settings_rejects_malformed_runtime_float_values tests/test_runtime.py::test_load_runtime_settings_reads_lifecycle_webhook_hmac_config tests/test_runtime.py::test_load_runtime_settings_reads_alert_webhook_config tests/test_runtime.py::test_load_runtime_settings_reads_public_web_worker_controls -q`
  - `18 passed`
- `python3 -m ruff check src tests`
  - `All checks passed!`
- `python3 -m mypy src tests`
  - `Success: no issues found in 174 source files`
- `python3 -m pytest tests/test_project_docs.py -q`
  - `326 passed`
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`
  - `1630 passed`
  - `Total coverage: 93.95%`
