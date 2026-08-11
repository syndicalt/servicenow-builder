# Sprint 363 Change Log

## Whole alert sink response diagnostic bounds

Hardened failed alert webhook diagnostics so the entire structured sink response is bounded after
recursive redaction. Sprint 362 capped individual response strings, but a failed alert sink could
still return a large JSON object or list containing many safe-looking entries. The runtime would
redact each entry and then format the whole structure into `AlertDeliveryError`, producing an
oversized worker warning or operator diagnostic.

Alert delivery now formats failed sink responses through one deterministic diagnostic formatter. It
recursively redacts the response, serializes it with compact sorted JSON, and caps the whole
diagnostic with `...[truncated]` before raising. This preserves the existing redaction behavior while
closing the aggregate structured-response path.

## Tests

- Failing-first coverage: 1 test failed before implementation, proving a failed alert sink could produce a 28 KB redacted `AlertDeliveryError` from one structured JSON response.
- Focused verification: `python3 -m pytest tests/test_alert_delivery.py -q -k "failure_redacts_sensitive_response_values or bounds_redacted_response or whole_structured_response"` passed with 3 tests.
- Alert regression verification: `python3 -m pytest tests/test_alert_delivery.py -q` passed with 23 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 187 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 187 source files, 437 documentation tests passed, and 2055 total tests passed at 94.04% coverage.
