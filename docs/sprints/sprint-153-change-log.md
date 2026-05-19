# Sprint 153 Change Log

## Form section edit handoff capability

- Added `form_section_remove` as a first-class form-layout capability for static section or tab removal requests.
- Classified the Demand story shape for hiding Assessment and Financials tabs on `dmn_demand` as a form section edit, not a UI Policy request.
- Added structured intent support for `Target artifact type: Form Section Removal`, `View`, and `Sections`.
- Added `form_sections` as a ServiceNow surface context, backed by retrieved `sys_ui_section` and `sys_ui_element` data.
- Added `form-layout-analysis-v1` worker artifacts so form section requests record existing sections and elements for human review.
- Enabled deterministic retrieved Update Set handoff for narrow form section removal. The app does not call the model for this path; it resolves named `sys_ui_section` records from live context, fails closed on missing or ambiguous sections, and emits reviewed `DELETE` customer updates for ServiceNow preview and commit.

## Verification

- `pytest tests/test_capabilities.py tests/test_capability_analysis.py tests/test_automation_intent.py tests/test_instance_discovery.py tests/test_implementation_packet.py tests/test_model_fulfillment.py tests/test_update_set_handoff.py tests/test_runtime.py tests/test_project_docs.py -q`
