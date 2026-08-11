# Sprint 365 Change Log

## JSON-safe alert sink diagnostics

Hardened failed alert sink diagnostics so non-JSON nested values cannot break the controlled
`AlertDeliveryError` path. Sprint 363 introduced deterministic JSON formatting for failed alert
responses, and Sprint 364 bounded traversal before formatting. If a transport or parser supplied a
non-JSON nested value such as `bytes` or an arbitrary Python object, however, `json.dumps()` could
raise `TypeError` and bypass the controlled alert diagnostic.

Alert response diagnostic projection now preserves normal JSON scalars after redaction and replaces
non-JSON values with a `non_json_type` marker. It does not call `repr()` or `str()` on arbitrary
objects, so binary payloads and object internals do not leak into worker warnings or operator
diagnostics.

## Tests

- Failing-first coverage: 1 test failed before implementation, proving a failed alert sink response containing `bytes` raised `TypeError` instead of controlled `AlertDeliveryError`.
- Focused verification: `python3 -m pytest tests/test_alert_delivery.py -q -k "non_json_response_values or does_not_consume_all_fields or whole_structured_response or bounds_redacted_response"` passed with 4 tests.
- Alert regression verification: `python3 -m pytest tests/test_alert_delivery.py -q` passed with 25 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 187 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 187 source files, 439 documentation tests passed, and 2059 total tests passed at 93.99% coverage.
