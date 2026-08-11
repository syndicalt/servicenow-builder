# Sprint 932 Change Log - Writeback batch report scalar-subclass diagnostic boundary

## Scope
- Hardened `_diagnostic_report_value()` for writeback batch report scalar diagnostics.
- Added a failing-first regression for hostile scalar-subclass report values.
- Documented the exact JSON scalar boundary for batch report diagnostics.

## Production Hardening
- Batch report diagnostics preserve exact booleans, exact integers, finite floats, exact strings, nulls, arrays, tuples, and dictionaries after redaction and traversal.
- Boolean and integer subclasses render as `[non-json value]` instead of being preserved as ordinary report booleans or numbers.
- The projector does not call `str()` or `repr()` on malformed scalar subclasses before report artifact output.

## Tests
- Added `test_build_writeback_batch_report_rejects_scalar_subclass_diagnostics`.
- Added `test_sprint_932_documents_writeback_batch_report_scalar_subclass_boundary`.
- Captured 1 failing-first writeback batch report scalar-subclass assertion.
- Focused verification: `2 passed`.
- Scoped verification: `tests/test_writeback_orchestration.py` passed with 28 tests and `tests/test_project_docs.py` passed with 1005 tests.
- Static verification: `python3 -m ruff check src tests` and `python3 -m mypy src tests` passed.
- Full coverage verification: `3574 passed`; total coverage remained 93.53%.
