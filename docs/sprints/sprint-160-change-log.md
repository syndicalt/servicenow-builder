# Sprint 160 Change Log

## Summary

- Added split ServiceNow runtime configuration for separate story/source and development/target instances.
- Added `SERVICENOW_PM_INSTANCE_URL`, `SERVICENOW_PM_CLIENT_ID`, and `SERVICENOW_PM_CLIENT_SECRET` for the PM story source.
- Added `SERVICENOW_DEV_INSTANCE_URL`, `SERVICENOW_DEV_CLIENT_ID`, and `SERVICENOW_DEV_CLIENT_SECRET` for the development target.
- Kept legacy `SERVICENOW_INSTANCE_URL`, `SERVICENOW_CLIENT_ID`, and `SERVICENOW_CLIENT_SECRET` as a single-instance compatibility fallback.
- Routed story retrieval, story state choices, story dictionary metadata, story AI status, work notes, and failure writeback through the PM client.
- Routed live development context retrieval, platform metadata reads, platform upserts, and retrieved Update Set imports through the DEV client.
- Updated `.env.example`, operator documentation, and system architecture documentation.

## Verification

- `pytest tests/test_runtime.py::test_load_runtime_settings_separates_pm_source_from_dev_target tests/test_runtime.py::test_split_servicenow_client_routes_story_and_development_operations tests/test_quality_gate.py::test_env_example_documents_required_servicenow_keys tests/test_project_docs.py::test_system_architecture_doc_includes_workflow_and_data_flow_diagrams -q`
