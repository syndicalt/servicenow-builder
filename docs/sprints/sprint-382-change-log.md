# Sprint 382 Change Log

## Sanitized external-build ServiceNow work notes

Hardened external-build writeback work-note construction so untrusted build tool output cannot inject raw secrets, control characters, or oversized text into ServiceNow work notes. The previous `_work_notes()` path appended `ExternalBuildResult.build_reference` and `ExternalBuildResult.message` directly to the human-readable work note.

External build work-note values now pass through diagnostic redaction, whitespace/control-character collapse, and a 500-character cap including the truncation marker before they are appended to ServiceNow work notes. Structured fields such as `u_ai_build_reference` still carry the original build reference for audit correlation and remain governed by the structured-field allowlist.

## Tests

- Failing-first coverage: 2 tests failed before implementation, proving external build references and messages could leak secret-like fragments, newlines, and oversized text into ServiceNow work notes.
- Focused verification: `python3 -m pytest tests/test_writeback.py -q -k "external_build_work_notes"` passed with 2 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 189 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 189 source files, 456 documentation tests passed, and 2111 total tests passed at 93.90% coverage.
