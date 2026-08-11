# Sprint 378 Change Log

## Sanitized manual-review automation feedback

Hardened manual-review automation feedback before it becomes candidate reviewer notes, artifacts, worker diagnostics, or ServiceNow work notes. The manual-review path previously converted `operator_feedback` entries with `str()` and appended `suggested_story` with raw newlines, which meant non-string objects, secret-like fragments, long suggested rewrites, and control-character-bearing text could pass into operator-facing notes.

Automation feedback now accepts only string feedback entries, skips non-string values instead of stringifying object internals, redacts secret-like fragments, collapses whitespace/control characters, and caps each feedback note at 2,000 characters including the truncation marker. Suggested-story feedback is emitted as a single sanitized `Suggested rewrite: ...` note.

## Tests

- Failing-first coverage: 2 tests failed before implementation, proving raw operator feedback and suggested-story text could leak secret-like fragments, newlines, object internals, and unbounded text into reviewer notes.
- Focused verification: `python3 -m pytest tests/test_implementation_packet.py -q -k "automation_feedback_notes"` passed with 2 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 189 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 189 source files, 452 documentation tests passed, and 2098 total tests passed at 93.91% coverage.
