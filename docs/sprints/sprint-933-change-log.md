# Sprint 933 Change Log - Admin artifact payload scalar-subclass diagnostic boundary

## Scope
- Hardened `_bounded_redacted_artifact_payload_node()` for admin artifact payload scalar diagnostics.
- Added a failing-first regression for hostile scalar-subclass artifact payload values.
- Documented the exact JSON scalar boundary for admin artifact diagnostic payloads.

## Production Hardening
- Admin artifact payload views preserve exact strings, exact booleans, exact integers, finite floats, nulls, arrays, tuples, and dictionaries after redaction and traversal.
- String, boolean, and integer subclasses render as `[non-json value]` instead of entering string redaction or being preserved as ordinary report booleans or numbers.
- The projector does not call `str()`, `repr()`, or string subclass methods on malformed scalar subclasses before artifact API serialization or HTML rendering.

## Tests
- Added `test_artifact_payload_view_rejects_scalar_subclass_values`.
- Added `test_sprint_933_documents_admin_artifact_payload_scalar_subclass_boundary`.
- Captured 1 failing-first admin artifact payload scalar-subclass assertion.
- Focused verification: `2 passed`.
- Scoped verification: `tests/test_runtime.py` passed with 421 tests and `tests/test_project_docs.py` passed with 1006 tests.
- Static verification: `python3 -m ruff check src tests` and `python3 -m mypy src tests` passed.
- Full coverage verification: `3576 passed`; total coverage remained 93.53%.
