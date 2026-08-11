# Sprint 374 Change Log

## Sanitized implementation-packet validation diagnostics

Hardened implementation-packet validation diagnostics so model-provided safety decisions and model-proposed table names cannot inject log lines or echo secret-like fragments when packet validation raises `ModelResponseError`. Previous provider-boundary hardening sanitized provider policy and generic response diagnostics, but packet validation still reflected unsupported safety decision values and unexpected table names directly.

Unsupported safety decisions and capability/table mismatch values now reuse the shared model-response diagnostic sanitizer. The validator still fails closed on unsupported decisions and table mismatches, but diagnostic values are redacted, whitespace/control-character-normalized, and capped before they are written to worker logs, artifacts, or ServiceNow work notes.

## Tests

- Failing-first coverage: 2 tests failed before implementation, proving unsupported safety decisions and capability/table mismatches could echo secret-like values and newline injection in `ModelResponseError` diagnostics.
- Focused verification: `python3 -m pytest tests/test_packet_validation.py -q` passed with 2 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 189 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 189 source files, 448 documentation tests passed, and 2084 total tests passed at 93.88% coverage.
