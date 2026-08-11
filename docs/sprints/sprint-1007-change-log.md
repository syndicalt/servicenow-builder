# Sprint 1007 Change Log - Employee Center discovery record collection guard

## Summary

Hardened Catalog and Employee Center context discovery so bespoke Employee Center topic and connected-content lookups validate live ServiceNow result containers before topic rendering, content-type filtering, citation counts, or context dossier assembly.

## Security

`_employee_center_topics_surface()` and `_employee_center_connected_content_surface()` now route `taxonomy`, `topic`, `taxonomy_content_configuration`, and `m2m_connected_content` fetch results through the shared `_surface_records()` boundary.

The helper accepts only exact Python lists containing exact Python dictionaries and fails closed with `discovery text metadata contains non-JSON value`.

Malformed Employee Center discovery containers fail before list iteration, `len()` hooks, record `.get()` hooks, active-state parsing, topic metadata extraction, content-type filtering, citation count calculation, missing-surface decisions, context dossier persistence, model invocation, ServiceNow import, or story writeback can consume caller-controlled container behavior.

## Tests

- Added 1 failing-first Employee Center topic record collection subclass assertion: `test_employee_center_topics_rejects_record_collection_subclass_without_leak`.
- Added 1 failing-first Employee Center topic record subclass assertion: `test_employee_center_topics_rejects_record_subclass_without_leak`.
- Added 1 documentation assertion: `test_sprint_1007_documents_employee_center_discovery_record_collection_guard`.

## Verification

- `pytest tests/test_instance_discovery.py::test_employee_center_topics_rejects_record_collection_subclass_without_leak tests/test_instance_discovery.py::test_employee_center_topics_rejects_record_subclass_without_leak -q` failed before implementation because unsafe list iteration and record `.get()` hooks executed.
- `pytest tests/test_instance_discovery.py::test_employee_center_topics_rejects_record_collection_subclass_without_leak tests/test_instance_discovery.py::test_employee_center_topics_rejects_record_subclass_without_leak tests/test_instance_discovery.py::test_discover_servicenow_surface_context_collects_catalog_employee_center_surfaces -q` - 3 passed.
