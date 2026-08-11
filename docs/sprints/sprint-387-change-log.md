# Sprint 387 Change Log

## Sanitized intake feedback work notes

Hardened intake feedback work-note construction so gate-failing story feedback cannot inject raw secrets, control characters, or oversized text into ServiceNow work notes. The previous `intake_feedback_work_note()` path appended story number, reason codes, operator guidance, and suggested rewrite text directly to the human-readable intake note, and it did not bound reason or guidance collections.

Intake feedback notes now use the shared `safe_work_note_value()` sanitizer for story number, reason codes, guidance, and suggested rewrite text. Reason-code and guidance collections are capped at 50 entries each, with fixed omitted-count markers for the rest. The durable intake feedback artifact still preserves the structured payload for audit correlation.

## Tests

- Failing-first coverage: 3 tests failed before implementation, proving intake feedback notes could leak secret-like fragments, preserve control-character formatting, emit oversized values, and include unbounded reason/guidance collections.
- Focused verification: `python3 -m pytest tests/test_capability_assessment.py -q` passed with 12 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 190 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 190 source files, 461 documentation tests passed, and 2127 total tests passed at 93.91% coverage.
