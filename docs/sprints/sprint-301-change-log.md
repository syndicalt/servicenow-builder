# Sprint 301 Change Log - Runtime Numeric Settings Load Guard

## Summary

- Runtime numeric settings loading now rejects padded or control-character env values before integer or float parsing.
- Integer settings such as rate limits, body-size limits, stale-job thresholds, HSTS max age, alert webhook max body bytes, and public-web byte/result limits must be base-10 integers without padding or control characters.
- Float timeout settings such as `JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS` and `JEDI_PUBLIC_WEB_TIMEOUT_SECONDS` must be finite numbers without padding or control characters.
- Malformed numeric diagnostics name only the setting and do not echo padded or control-character fragments.
- Existing malformed numeric and non-finite float validation remains intact.
- Added failing regressions proving padded numeric env values were previously accepted or downgraded to generic parser errors during settings loading.
- Documented the stricter runtime numeric settings-load boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "runtime_integer_values or runtime_float_values"` - 5 tests failed before implementation because padded numeric values were silently normalized or did not report the stricter diagnostic.
- `python3 -m pytest tests/test_runtime.py -q -k "runtime_integer_values or runtime_float_values"` - 22 passed after implementation.
- `python3 -m pytest tests/test_runtime.py -q` - 235 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_three_hundred_one_documents_runtime_numeric_load_guard -q` - 1 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 375 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1813 passed, total coverage 93.91%.
