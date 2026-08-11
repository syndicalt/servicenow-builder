# Sprint 1011 Change Log - Operational store surface maturity row guard

## Summary

Hardened operational-store surface maturity evidence so database aggregate rows are validated before automation maturity scoring or routing decisions consume them.

## Security

`builder_maturity_evidence_for_surface()` now routes the returned aggregate row through `_surface_maturity_count()`.

The helper accepts only exact Python dictionaries and exact integer values for `samples`, `successes`, and `failures`. Dictionary subclasses, mapping-like objects, boolean values, integer subclasses, floats, strings, and hostile numeric objects fail closed with `operational store surface maturity row contains non-JSON value`.

Malformed maturity evidence rows fail before row indexing hooks, numeric conversion hooks, maturity scoring, automation-threshold checks, admin reporting, or work-note routing can consume caller-controlled database row behavior.

## Tests

- Added 1 failing-first operational-store surface maturity row subclass assertion: `test_surface_maturity_evidence_rejects_row_subclass_without_leak`.
- Added 1 failing-first operational-store surface maturity count object assertion: `test_surface_maturity_evidence_rejects_count_object_without_leak`.
- Added 1 documentation assertion: `test_sprint_1011_documents_operational_store_surface_maturity_row_guard`.

## Verification

- `pytest tests/test_operational_store.py::test_surface_maturity_evidence_rejects_row_subclass_without_leak tests/test_operational_store.py::test_surface_maturity_evidence_rejects_count_object_without_leak -q` failed before implementation because unsafe row indexing and numeric conversion hooks executed.
- `pytest tests/test_operational_store.py::test_surface_maturity_evidence_rejects_row_subclass_without_leak tests/test_operational_store.py::test_surface_maturity_evidence_rejects_count_object_without_leak tests/test_operational_store.py::test_builder_maturity_evidence_for_surface_aggregates_terminal_outcomes -q` - 3 passed.
