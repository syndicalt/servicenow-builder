# Sprint 394 Change Log

## Non-empty artifact payload key diagnostics

Hardened admin artifact payload key rendering so keys that sanitize to an empty label do not appear as blank JSON object keys in diagnostic views. Persisted artifact keys containing only whitespace or control characters previously rendered as `""`; duplicate empty sanitized keys rendered with a leading-space suffix such as `" [duplicate 2]"`.

Admin artifact payload projection now replaces empty sanitized keys with `[empty key]` before duplicate detection and suffixing. This keeps JSON API and Basic-auth HTML diagnostics explicit, searchable, and non-ambiguous without changing the stored artifact payload.

## Tests

- Failing-first coverage: 1 test failed before implementation, proving whitespace/control-only persisted artifact keys rendered as empty diagnostic labels.
- Focused verification: `python3 -m pytest tests/test_runtime.py -q -k "payload_keys"` passed with 5 tests.
- Broader artifact verification: `python3 -m pytest tests/test_runtime.py -q -k "payload_keys or artifact_view or artifact_read or admin_console_artifact"` passed with 22 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 190 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 190 source files, 468 documentation tests passed, and 2146 total tests passed at 93.92% coverage.
