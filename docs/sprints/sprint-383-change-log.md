# Sprint 383 Change Log

## Sanitized build-claim ServiceNow work notes

Hardened build-claim writeback work-note construction so lifecycle event ids cannot inject raw secrets, control characters, or oversized text into ServiceNow work notes. The previous `_build_claim_work_notes()` path appended the lifecycle event id directly to the human-readable work note.

Build-claim lifecycle event ids now pass through diagnostic redaction, whitespace/control-character collapse, and a 500-character cap including the truncation marker before they are appended to ServiceNow work notes. Structured build-claim audit events continue to carry the original lifecycle event id for correlation.

## Tests

- Failing-first coverage: 2 tests failed before implementation, proving lifecycle event ids could leak secret-like fragments, newlines, and oversized text into ServiceNow work notes.
- Focused verification: `python3 -m pytest tests/test_writeback.py -q -k "build_claim"` passed with 4 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 189 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 189 source files, 457 documentation tests passed, and 2114 total tests passed at 93.90% coverage.
