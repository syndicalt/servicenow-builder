# Sprint 393 Change Log

## Bounded duplicate artifact payload keys

Hardened admin artifact payload key rendering so duplicate sanitized labels remain bounded after duplicate suffixing. Sprint 390 correctly sanitized and capped artifact payload dictionary keys before rendering, but the duplicate suffix was appended after that cap. Two distinct oversized persisted keys that collapsed to the same sanitized label could therefore produce a rendered key longer than the documented 500-character bound.

Duplicate sanitized payload keys now reserve space for both the truncation marker and deterministic duplicate suffix inside the same 500-character key budget. The suffix remains visible, and rendered diagnostic keys stay bounded.

## Tests

- Failing-first coverage: 1 test failed before implementation, proving duplicate sanitized artifact payload keys could exceed the 500-character diagnostic key bound.
- Focused verification: `python3 -m pytest tests/test_runtime.py -q -k "payload_keys"` passed with 4 tests.
- Broader artifact verification: `python3 -m pytest tests/test_runtime.py -q -k "payload_keys or artifact_view or artifact_read or admin_console_artifact"` passed with 21 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 190 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 190 source files, 467 documentation tests passed, and 2144 total tests passed at 93.90% coverage.
