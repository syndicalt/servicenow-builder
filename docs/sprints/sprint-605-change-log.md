# Sprint 605 Change Log

## Writeback batch report diagnostic key projection

Sprint 605 continued production hardening by making writeback batch report diagnostic dictionary keys stringification-safe. Batch report values were already redacted, whitespace-normalized, bounded, cycle-safe, depth-bounded, and non-JSON-safe, but dictionary keys inside diagnostic projections were still passed through `str(key)` before sanitization. A malformed key object could raise during report generation or surface unsafe stringification behavior before a write-once batch report artifact was produced.

`_diagnostic_report_node()` now delegates dictionary key rendering to `_diagnostic_report_key()`. Exact string keys continue through `structured_writeback_field_value()`, empty sanitized keys become `[empty key]`, and non-string keys become `[non-json key]` without calling `str()` or `repr()` on the original object.

Verification:

- Added 1 failing-first writeback batch report diagnostic-key test proving `build_writeback_batch_report()` called a hostile key object's `__str__()` before implementation.
- `python3 -m pytest tests/test_writeback_orchestration.py::test_build_writeback_batch_report_normalizes_non_string_diagnostic_keys -q`: failed before implementation because report generation raised `client_secret=writeback-key-str-secret` from the hostile key object's `__str__()`.
- `python3 -m pytest tests/test_writeback_orchestration.py::test_build_writeback_batch_report_normalizes_non_string_diagnostic_keys tests/test_writeback_orchestration.py::test_build_writeback_batch_report_redacts_diagnostic_values tests/test_writeback_orchestration.py::test_build_writeback_batch_report_handles_cyclic_and_deep_diagnostics tests/test_writeback_orchestration.py::test_build_writeback_batch_report_normalizes_unsupported_scalar_diagnostics -q`: 4 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_605_documents_writeback_batch_report_diagnostic_key_projection tests/test_project_docs.py::test_sprint_485_documents_writeback_batch_report_redaction tests/test_project_docs.py::test_sprint_487_documents_writeback_batch_report_scalar_normalization -q`: 3 passed.
- `python3 -m pytest tests/test_writeback_orchestration.py -q`: 25 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 679 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2688 passed, total coverage 93.17%, required 90% coverage reached.
