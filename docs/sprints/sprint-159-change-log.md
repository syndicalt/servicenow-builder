# Sprint 159 Change Log

## Summary

- Added the context-only `cmdb_ire_analyze` capability for CMDB Identification and Reconciliation Engine stories.
- Routed serial-number reconciliation and primary-identifier stories to CMDB IRE analysis instead of generic unknown or catalog-item reasoning.
- Added required live instance surfaces for IRE dossiers: `cmdb_ire_identification_rules`, `cmdb_ire_reconciliation_rules`, `cmdb_data_sources`, and `cmdb_class_hierarchy`.
- Added the persisted `cmdb_ire_analysis` artifact with schema `cmdb-ire-analysis-v1`.
- Kept the production boundary intact: CMDB IRE stories do not create retrieved Update Sets until deterministic validators and builder evidence are approved.
- Added `docs/system-architecture.md` with component, workflow, data-flow, model-flow, retrieved Update Set handoff, admin console, and failure-handling diagrams.

## Verification

- `pytest tests/test_capabilities.py::test_cmdb_ire_analysis_profile_is_context_only tests/test_capability_analysis.py::test_cmdb_ire_story_routes_to_context_analysis tests/test_instance_discovery.py::test_discover_servicenow_surface_context_collects_cmdb_ire_surfaces tests/test_model_fulfillment.py::test_model_fulfillment_can_disable_classifier_gate_for_exploratory_reasoning -q`
- `pytest tests/test_project_docs.py::test_system_architecture_doc_includes_workflow_and_data_flow_diagrams -q`
