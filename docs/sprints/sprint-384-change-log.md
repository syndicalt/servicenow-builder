# Sprint 384 Change Log

## Sanitized runtime failure ServiceNow work notes

Hardened runtime failure notification so failed fulfillment jobs cannot inject raw secrets, control characters, or oversized text into ServiceNow work notes. The previous `_servicenow_failure_notifier()` path redacted only configured literal secrets from the failure message, then appended the lifecycle event id, fulfillment job id, and error text directly to the human-readable failure note.

Introduced a shared `safe_work_note_value()` sanitizer for ServiceNow work-note values. Runtime failure notes now redact diagnostic secret patterns and configured literal secrets, collapse whitespace/control characters, and cap each lifecycle event id, job id, and failure message value at 500 characters including the truncation marker. The existing external-build and build-claim writeback paths now delegate to the shared sanitizer while preserving their structured audit fields.

## Tests

- Failing-first coverage: 2 tests failed before implementation, proving runtime failure notes could leak secret-like event ids, job ids, error fragments, newlines, and oversized values into ServiceNow work notes.
- Focused verification: `python3 -m pytest tests/test_runtime.py tests/test_writeback.py -q -k "servicenow_failure_notifier or work_notes"` passed with 6 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 190 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 190 source files, 458 documentation tests passed, and 2117 total tests passed at 93.91% coverage.
