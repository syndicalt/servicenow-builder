# Sprint 392 Change Log

## Enforced ASCII-only request IDs

Tightened runtime response correlation so inbound `X-Request-ID` values are preserved only when they use the intended ASCII token alphabet. Sprint 391 narrowed reflected request IDs to letters, digits, hyphen, underscore, and period, but Python `str.isalnum()` also accepts non-ASCII letters.

`X-JEDI-Request-ID` now preserves inbound request IDs only when every character is ASCII and part of the approved token alphabet. Non-ASCII request IDs are rejected by the same guard and replaced with a generated UUID.

## Tests

- Failing-first coverage: 1 test failed before implementation, proving `_safe_request_id()` accepted a non-ASCII letter in an inbound request ID.
- Focused verification: `python3 -m pytest tests/test_runtime.py -q -k "request_id"` passed with 6 tests.
- Adjacent header verification: `python3 -m pytest tests/test_runtime.py -q -k "request_id or security_headers or robot_indexing or vary_by_authorization"` passed with 14 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 190 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 190 source files, 466 documentation tests passed, and 2142 total tests passed at 93.90% coverage.
