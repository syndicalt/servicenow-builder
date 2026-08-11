# Sprint 381 Change Log

## Sanitized manual-review ServiceNow work notes

Hardened manual-review ServiceNow work-note construction so malformed candidate metadata cannot leak raw text, crash feedback generation, or create oversized work notes. The previous `_manual_feedback_fields()` path joined `eligibility_reasons` directly, selected reviewer notes with raw `.strip()`, and included missing-context names without redaction or bounds. A malformed candidate assembled outside the normal validated model path could therefore inject newlines, secret-like fragments, object internals, or very large strings into ServiceNow work notes.

Manual-review work notes now sanitize eligibility reasons, missing-context names, and actionable reviewer notes at the final writeback boundary. Non-string values are skipped, secret-like fragments are redacted, whitespace/control characters are collapsed, each emitted value is capped at 500 characters including the truncation marker, and at most 50 reasons or 50 actionable reviewer notes are included with omitted-count markers for additional values.

## Tests

- Failing-first coverage: 2 tests failed before implementation, proving malformed candidate reasons could crash work-note construction and oversized reasons/reviewer notes could create unbounded ServiceNow work-note text.
- Focused verification: `python3 -m pytest tests/test_model_fulfillment.py -q -k "manual_work_note"` passed with 2 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 189 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 189 source files, 455 documentation tests passed, and 2108 total tests passed at 93.90% coverage.
