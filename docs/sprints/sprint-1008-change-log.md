# Sprint 1008 Change Log - CMDB IRE discovery record collection guard

## Summary

Hardened CMDB IRE context discovery so bespoke identification-rule and class-hierarchy lookups validate live ServiceNow result containers before IRE rule rendering, class filtering, citation counts, or context dossier assembly.

## Security

`_cmdb_ire_identification_rules_surface()` and `_cmdb_class_hierarchy_surface()` now route `cmdb_identifier`, `cmdb_identifier_entry`, and `sys_db_object` fetch results through the shared `_surface_records()` boundary.

The helper accepts only exact Python lists containing exact Python dictionaries and fails closed with `discovery text metadata contains non-JSON value`.

Malformed CMDB IRE discovery containers fail before list iteration, `len()` hooks, record `.get()` hooks, active-state parsing, rule metadata extraction, CMDB class filtering, citation count calculation, context dossier persistence, model invocation, ServiceNow import, or story writeback can consume caller-controlled container behavior.

## Tests

- Added 1 failing-first CMDB IRE record collection subclass assertion: `test_cmdb_ire_identification_rejects_record_collection_subclass_without_leak`.
- Added 1 failing-first CMDB IRE record subclass assertion: `test_cmdb_ire_identification_rejects_record_subclass_without_leak`.
- Added 1 documentation assertion: `test_sprint_1008_documents_cmdb_ire_discovery_record_collection_guard`.

## Verification

- `pytest tests/test_instance_discovery.py::test_cmdb_ire_identification_rejects_record_collection_subclass_without_leak tests/test_instance_discovery.py::test_cmdb_ire_identification_rejects_record_subclass_without_leak -q` failed before implementation because unsafe list iteration and record `.get()` hooks executed.
- `pytest tests/test_instance_discovery.py::test_cmdb_ire_identification_rejects_record_collection_subclass_without_leak tests/test_instance_discovery.py::test_cmdb_ire_identification_rejects_record_subclass_without_leak tests/test_instance_discovery.py::test_discover_servicenow_surface_context_collects_cmdb_ire_surfaces -q` - 3 passed.
