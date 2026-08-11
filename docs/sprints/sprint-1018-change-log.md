# Sprint 1018 Change Log - Surface maturity evidence record guard

## Summary
Hardened surface maturity evidence record hydration so automation-threshold evidence is exact-scalar validated wherever the DTO is constructed.

## Security
`SurfaceMaturityEvidenceRecord` now requires an exact string surface name and exact non-negative integer `samples`, `successes`, and `failures` counts.

Malformed maturity evidence values fail closed with `operational store surface maturity record scalar is unsafe` before Pydantic coercion, maturity scoring, automation-threshold decisions, admin reporting, API serialization, or work-note routing can turn malformed scoring evidence into official maturity state.

## Tests
- Added 1 failing-first surface maturity evidence text subclass assertion: `test_surface_maturity_evidence_record_rejects_surface_string_subclass_without_leak`.
- Added 1 invalid surface maturity evidence count scalar matrix: `test_surface_maturity_evidence_record_rejects_invalid_count_scalars`.
- Added 1 documentation assertion: `test_sprint_1018_documents_surface_maturity_evidence_record_guard`.

## Verification
- `pytest tests/test_operational_store.py::test_surface_maturity_evidence_record_rejects_surface_string_subclass_without_leak tests/test_operational_store.py::test_surface_maturity_evidence_record_rejects_invalid_count_scalars -q` failed before implementation because Pydantic accepted unsafe maturity evidence inputs.
- `pytest tests/test_operational_store.py::test_surface_maturity_evidence_record_rejects_surface_string_subclass_without_leak tests/test_operational_store.py::test_surface_maturity_evidence_record_rejects_invalid_count_scalars tests/test_operational_store.py::test_builder_maturity_evidence_for_surface_aggregates_terminal_outcomes tests/test_operational_store.py::test_surface_maturity_evidence_rejects_count_object_without_leak -q` - 5 passed.
