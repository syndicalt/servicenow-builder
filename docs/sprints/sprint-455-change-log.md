# Sprint 455 Change Log

## Alert sink response non-JSON type-name suppression

Hardened alert sink response diagnostics so unsupported scalar values no longer expose Python type names. Prior behavior avoided `repr()` but emitted structured `non_json_type` markers such as `bytes` and `object`. That still reflected implementation details from alternate transports and made operator diagnostics depend on Python runtime types.

Unsupported alert sink response values now render as `[non-json value]`. Normal JSON scalars are preserved, strings are still redacted and bounded, and the existing response key sanitization, cycle handling, depth cap, width bounds, and whole-diagnostic cap remain intact.

## Verification

- Updated 1 failing-first alert response diagnostic test covering non-JSON bytes and object values.
- `python3 -m pytest tests/test_alert_delivery.py -q -k "non_json_response_values"`: failed before implementation because `non_json_type` and Python type names reached `AlertDeliveryError`.
- `python3 -m pytest tests/test_alert_delivery.py -q -k "non_json_response_values or excessive_response_depth or circular_response_payloads or sensitive_response_keys or non_string_response_keys or alert_response_diagnostic_does_not_consume_all_fields"`: 6 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 195 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 529 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2348 total tests passed at 93.79% coverage.
