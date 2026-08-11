# Sprint 377 Change Log

## Bounded implementation-packet review note content

Hardened implementation-packet review-note validation so a single model-generated `test_plan` or `rollback_notes` item cannot carry oversized text or control-character injection into candidate reviewer notes, artifacts, worker logs, or ServiceNow work notes. Sprint 376 bounded the number of review items and required strings, but each individual string was still unbounded and could contain newlines or other control characters.

Review-note items are now limited to 2,000 characters and must not contain ASCII control characters. Violations fail closed with fixed diagnostics such as `test_plan item exceeds length limit (max 2000)` or `test_plan items must not contain control characters`; rejected model-provided note content is not echoed.

## Tests

- Failing-first coverage: 2 tests failed before implementation, proving oversized review-note strings and control-character-bearing review notes were accepted by implementation-packet validation.
- Focused verification: `python3 -m pytest tests/test_packet_validation.py -q` passed with 10 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 189 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 189 source files, 451 documentation tests passed, and 2095 total tests passed at 93.91% coverage.
