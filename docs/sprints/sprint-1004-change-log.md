# Sprint 1004 Change Log - Dictionary/form discovery record collection guard

## Summary

Hardened dictionary/form context discovery so live ServiceNow table, dictionary, form section, form element, and ACL metadata result containers are validated before context dossier assembly.

## Security

`discover_dictionary_form_context()` now routes `sys_db_object`, `sys_dictionary`, `sys_ui_section`, `sys_ui_element`, and `sys_security_acl` `fetch_table_records()` responses through `_metadata_records()`.

The helper accepts only exact Python lists containing exact Python dictionaries and fails closed with `dictionary/form discovery metadata contains non-JSON value`.

Malformed metadata result containers fail before truthiness checks, indexing, list iteration, record `.get()` hooks, table schema extraction, form-layout extraction, ACL indicator collection, context dossier persistence, model invocation, ServiceNow import, or story writeback can consume caller-controlled container behavior.

## Tests

- Added 1 failing-first dictionary/form discovery record collection subclass assertion: `test_discover_dictionary_form_context_rejects_record_collection_subclass_without_leak`.
- Added 1 failing-first dictionary/form discovery record subclass assertion: `test_discover_dictionary_form_context_rejects_record_subclass_without_leak`.
- Added 1 documentation assertion: `test_sprint_1004_documents_dictionary_form_discovery_record_collection_guard`.

## Verification

- `pytest tests/test_instance_discovery.py::test_discover_dictionary_form_context_rejects_record_collection_subclass_without_leak tests/test_instance_discovery.py::test_discover_dictionary_form_context_rejects_record_subclass_without_leak -q` failed before implementation because unsafe list iteration and record `.get()` hooks executed.
- `pytest tests/test_instance_discovery.py::test_discover_dictionary_form_context_rejects_record_collection_subclass_without_leak tests/test_instance_discovery.py::test_discover_dictionary_form_context_rejects_record_subclass_without_leak tests/test_instance_discovery.py::test_discover_dictionary_form_context_fetches_target_instance_state -q` - 3 passed.
