# Sprint 370 Change Log

## Anthropic structured error metadata redaction

Hardened Anthropic provider error diagnostics so structured `error.type` metadata cannot inject log lines or echo the configured Anthropic API key. Previous controls redacted and bounded free-form Messages API error text and sanitized request-id headers, but `error.type` was appended directly to provider errors.

Structured Anthropic error type values now pass through provider diagnostic redaction and whitespace/control-character normalization before inclusion. Useful `type=<value>` operator context is preserved, but newlines, tabs, sensitive assignments, and configured API key echoes are removed before the final provider diagnostic cap.

## Tests

- Failing-first coverage: 1 test failed before implementation, proving raw Anthropic `error.type` metadata could inject a newline into provider diagnostics.
- Focused verification: `python3 -m pytest tests/test_anthropic_provider.py -q -k "sanitizes_structured_error_type or reports_error_type_without_message or redacts_and_bounds_error_details or sanitizes_request_id"` passed with 4 tests.
- Anthropic regression verification: `python3 -m pytest tests/test_anthropic_provider.py -q` passed with 71 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 187 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 187 source files, 444 documentation tests passed, and 2071 total tests passed at 93.80% coverage.
