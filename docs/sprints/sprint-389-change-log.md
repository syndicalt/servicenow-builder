# Sprint 389 Change Log

## Sanitized CLI summary output

Hardened shared CLI summary rendering so report-derived summary keys and values cannot inject raw secrets, control characters, or oversized text into operator terminals or CI logs. The previous `render_summary()` path appended mapping keys and values directly into `key=value` output.

CLI summaries now use the shared `safe_work_note_value()` sanitizer for each key and value before formatting. Normal summary output remains unchanged, while malformed or untrusted report payload values are redacted, whitespace/control-character-normalized, and capped at 500 characters including the truncation marker.

## Tests

- Failing-first coverage: 2 tests failed before implementation, proving CLI summary keys and values could leak secret-like fragments, preserve control-character formatting, and emit oversized values into terminal output.
- Focused verification: `python3 -m pytest tests/test_cli_io.py -q` passed with 6 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 190 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 190 source files, 463 documentation tests passed, and 2133 total tests passed at 93.91% coverage.
