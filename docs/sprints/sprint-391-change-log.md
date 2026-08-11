# Sprint 391 Change Log

## Hardened reflected request IDs

Hardened runtime response correlation so `X-JEDI-Request-ID` does not reflect arbitrary inbound `X-Request-ID` header text. The prior guard accepted any visible ASCII up to 128 characters, which allowed whitespace, separators, and secret-like assignment fragments to be copied into response headers.

Inbound request IDs are now preserved only when they are 1 to 128 characters and contain letters, digits, hyphen, underscore, or period. Unsafe request IDs are replaced with a generated UUID. Existing safe edge IDs such as `edge-request-01` remain supported.

## Tests

- Failing-first coverage: 2 tests failed before implementation, proving sensitive assignment fragments and whitespace-bearing request IDs were reflected in `X-JEDI-Request-ID`.
- Focused verification: `python3 -m pytest tests/test_runtime.py -q -k "request_id"` passed with 5 tests.
- Adjacent header verification: `python3 -m pytest tests/test_runtime.py -q -k "request_id or security_headers or robot_indexing or vary_by_authorization"` passed with 13 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 190 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 190 source files, 465 documentation tests passed, and 2140 total tests passed at 93.90% coverage.
