# Sprint 1005 Change Log - Shared surface discovery record collection guard

## Summary

Hardened shared ServiceNow surface discovery so fetched and pre-collected platform surface records are validated before non-form context dossier assembly.

## Security

`_table_surface()` and `_records_surface()` now route ServiceNow surface record collections through `_surface_records()`.

The helper accepts only exact Python lists containing exact Python dictionaries and fails closed with `discovery text metadata contains non-JSON value`.

Malformed surface record containers fail before list iteration, record `.get()` hooks, active-state parsing, name extraction, summary extraction, metadata minimization, citation count calculation, context dossier persistence, model invocation, ServiceNow import, or story writeback can consume caller-controlled container behavior.

## Tests

- Added 1 failing-first shared surface discovery record collection subclass assertion: `test_discover_surface_context_rejects_record_collection_subclass_without_leak`.
- Added 1 failing-first shared surface discovery record subclass assertion: `test_discover_surface_context_rejects_record_subclass_without_leak`.
- Added 1 documentation assertion: `test_sprint_1005_documents_shared_surface_discovery_record_collection_guard`.

## Verification

- `pytest tests/test_instance_discovery.py::test_discover_surface_context_rejects_record_collection_subclass_without_leak tests/test_instance_discovery.py::test_discover_surface_context_rejects_record_subclass_without_leak -q` failed before implementation because unsafe list iteration and record `.get()` hooks executed.
- `pytest tests/test_instance_discovery.py::test_discover_surface_context_rejects_record_collection_subclass_without_leak tests/test_instance_discovery.py::test_discover_surface_context_rejects_record_subclass_without_leak tests/test_instance_discovery.py::test_discover_servicenow_surface_context_collects_related_platform_surfaces -q` - 3 passed.
