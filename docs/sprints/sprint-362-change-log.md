# Sprint 362 Change Log

## Alert sink response diagnostic bounds

Hardened external alert delivery errors so a failing alert sink cannot return an oversized
diagnostic string after redaction. Alert sink response bodies were already recursively redacted for
secret-bearing keys and diagnostic strings, but long redacted strings were embedded at full length in
`AlertDeliveryError`. Those errors can surface in worker warning logs and operator diagnostics.

Alert response string diagnostics now apply a post-redaction size cap and use `...[truncated]` when
the redacted sink response is too large. The control preserves the existing structured response
redaction behavior and applies only to diagnostics generated from failed alert sink responses.

## Tests

- Failing-first coverage: 1 test failed before implementation, proving a failed alert sink could return a redacted but oversized response string inside `AlertDeliveryError`.
- Focused verification: `python3 -m pytest tests/test_alert_delivery.py -q -k "failure_redacts_sensitive_response_values or bounds_redacted_response"` passed with 2 tests.
- Alert regression verification: `python3 -m pytest tests/test_alert_delivery.py -q` passed with 22 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 187 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 187 source files, 436 documentation tests passed, and 2053 total tests passed at 94.02% coverage.
