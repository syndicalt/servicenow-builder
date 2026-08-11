# Sprint 390 Change Log

## Sanitized admin artifact payload keys

Hardened admin artifact payload rendering so persisted artifact dictionary keys cannot inject raw secrets, control characters, or oversized labels into JSON API responses or the Basic-auth HTML artifact view. Artifact payload values were already redacted and bounded, but keys from durable artifact records were still treated as trusted labels.

Admin artifact payload projection now sanitizes dictionary keys with the shared `safe_work_note_value()` boundary before rendering. Secret-like assignment fragments in keys are redacted, whitespace and control characters are collapsed, and each key is capped at 500 characters including the truncation marker. If multiple original keys collapse to the same sanitized label, the later rendered keys receive deterministic duplicate suffixes instead of overwriting diagnostic content.

## Tests

- Failing-first coverage: 3 tests failed before implementation, proving JSON and HTML admin artifact views could leak secret-bearing payload keys and render oversized key labels.
- Focused verification: `python3 -m pytest tests/test_runtime.py -q -k "payload_keys"` passed with 3 tests.
- Broader artifact verification: `python3 -m pytest tests/test_runtime.py -q -k "artifact_view or artifact_read or admin_console_artifact"` passed with 20 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 190 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 190 source files, 464 documentation tests passed, and 2137 total tests passed at 93.90% coverage.
