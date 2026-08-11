# Sprint 385 Change Log

## Sanitized runtime completion ServiceNow work notes

Hardened runtime completion closeout so completed-story lifecycle events cannot inject raw secrets, control characters, or oversized text into ServiceNow work notes. The previous `_servicenow_complete_notifier()` path appended the completion lifecycle event id directly to the human-readable closeout note.

Completion lifecycle event ids now pass through the shared `safe_work_note_value()` sanitizer before writeback. The value is redacted for diagnostic secret patterns, whitespace/control characters are collapsed, and the emitted value is capped at 500 characters including the truncation marker.

## Tests

- Failing-first coverage: 2 tests failed before implementation, proving completion lifecycle event ids could leak secret-like fragments, newlines, and oversized values into ServiceNow closeout work notes.
- Focused verification: `python3 -m pytest tests/test_runtime.py -q -k "servicenow_complete_notifier or runtime_complete_event_updates_ai_status"` passed with 3 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 190 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 190 source files, 459 documentation tests passed, and 2120 total tests passed at 93.91% coverage.
