# Sprint 155 Change Log

## Form layout surface-operation planner

- Added a `surface_planning` contract so flexible ServiceNow requests can be represented as surface operations instead of one-off classifier branches.
- Introduced the `form_layout` surface and operation names:
  - `form_layout.section.remove`
  - `form_layout.section.add`
  - `form_layout.section.rename`
  - `form_layout.section.reorder`
- Kept only `form_layout.section.remove` supported at runtime.
- Migrated the existing form-section removal candidate path to use the planned supported operation while preserving the existing retrieved Update Set XML handoff.
- Recognized add, rename, and reorder as known unsupported form-layout operations, routing them to manual review with stable `unsupported surface operation` reasons instead of treating them as unknown classifier failures or accidental deletes.
- Preserved the ServiceNow preview/commit review boundary and did not add new mutation builders.

## Verification

- `pytest tests/test_surface_planning.py tests/test_implementation_packet.py::test_form_section_remove_candidate_uses_surface_operation_plan tests/test_implementation_packet.py::test_unsupported_form_layout_surface_operation_routes_to_manual_review -q`
