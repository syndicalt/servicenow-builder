# Sprint 154 Change Log

## Form section removal gate hardening

- Tightened structured intent classification for generic `Form Section` and `Form Tabs` stories.
- Kept explicit `Form Section Removal` stories supported for narrow remove/hide/not-display requests.
- Required generic form-section stories to include a clear remove, hide, or not-display action before they can enter the `form_section_remove` delete pipeline.
- Routed rename/add/reorder style form-section requests away from the removal builder instead of treating them as `sys_ui_section` DELETE work.
- Preserved the existing retrieved Update Set review boundary and did not add a new mutation surface.

## Verification

- `pytest tests/test_automation_intent.py::test_extracts_generic_form_section_intent_only_when_action_is_removal tests/test_automation_intent.py::test_rejects_generic_form_section_intent_without_removal_action tests/test_capability_analysis.py::test_structured_form_section_rename_does_not_route_to_removal_pipeline -q`
