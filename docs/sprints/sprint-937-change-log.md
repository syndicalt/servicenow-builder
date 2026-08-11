# Sprint 937 Change Log - Admin artifact payload exact-container diagnostic boundary

## Scope
- Hardened `_bounded_redacted_artifact_payload_node()` to traverse only exact dictionaries, lists, and tuples.
- Preserved wide admin artifact payload truncation coverage using an ordinary dictionary instead of a subclass probe.
- Documented the exact-container boundary for admin artifact diagnostic payload views.

## Production Hardening
- Admin artifact payload diagnostic views now treat container subclasses as malformed diagnostic values.
- Dictionary, list, and tuple subclasses render as `[non-json value]` before `items()`, `len()`, iteration, or subclass hooks can execute.
- Ordinary exact dictionaries, lists, and tuples still retain bounded traversal, cycle handling, depth handling, duplicate-key handling, and truncation markers.

## Tests
- Added `test_artifact_payload_view_rejects_container_subclasses`.
- Added `test_sprint_937_documents_admin_artifact_payload_exact_container_boundary`.
- Captured 1 failing-first admin artifact payload container-subclass assertion.
- Focused verification: `5 passed`.
- Scoped verification: `tests/test_runtime.py` passed with 424 tests and `tests/test_project_docs.py` passed with 1010 tests.
- Static verification: `python3 -m ruff check src tests` and `python3 -m mypy src tests` passed.
- Full coverage verification: `3587 passed`; total coverage remained 93.57%.
