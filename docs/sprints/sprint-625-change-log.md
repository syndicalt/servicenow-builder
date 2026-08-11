# Sprint 625 Change Log

## Writeback batch report exact-string diagnostic values

Sprint 625 continued production hardening by aligning writeback batch report diagnostic values with the existing exact-string key projection. `_diagnostic_report_value()` already redacted ordinary strings, normalized unsupported scalar values to `[non-json value]`, and projected dictionary keys without stringifying malformed objects, but string subclasses still took the string-value path and could return a work-note-specific marker instead of the batch report scalar marker.

Batch report diagnostic values now accept exact `str` instances only. String subclasses render as `[non-json value]`, matching unsupported scalar behavior and keeping writeback batch report artifacts independent of work-note-specific fallback labels.

Verification:

- Added 1 failing-first writeback orchestration test proving string subclass diagnostics used the string-value path before implementation.
- `python3 -m pytest tests/test_writeback_orchestration.py::test_build_writeback_batch_report_rejects_string_subclass_diagnostics -q`: failed before implementation because the diagnostic returned `[non-string work note value]` instead of `[non-json value]`.
- `python3 -m pytest tests/test_writeback_orchestration.py -q`: 27 tests passed.
- `python3 -m pytest tests/test_writeback_orchestration.py tests/test_project_docs.py::test_sprint_625_documents_writeback_batch_report_exact_string_values -q`: 28 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 699 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed with no issues in 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2737 tests passed at 93.05% coverage.
