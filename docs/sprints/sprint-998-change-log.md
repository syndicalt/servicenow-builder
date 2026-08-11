# Sprint 998 Change Log - Update Set importer apply response guard

## Summary

Hardened Update Set importer bootstrap apply so ServiceNow upsert response containers are validated before response-field access.

## Security

`apply_update_set_importer_records()` now routes `sys_ws_definition` and `sys_ws_operation` upsert responses through `_update_set_importer_upsert_result()`.

The helper accepts only exact Python dictionaries and fails closed with `Update Set importer lookup contains non-JSON value`.

Malformed upsert response containers fail before `.get()` hooks, dependent operation upserts, `sys_id` extraction, apply-result recording, object representations, bytes, containers, or credential-like response fragments can be consumed or exposed.

## Tests

- Added 1 failing-first Update Set importer definition response subclass assertion: `test_apply_update_set_importer_records_rejects_definition_response_subclass`.
- Added 1 failing-first Update Set importer operation response subclass assertion: `test_apply_update_set_importer_records_rejects_operation_response_subclass`.
- Added 1 documentation assertion: `test_sprint_998_documents_update_set_importer_apply_response_guard`.

## Verification

- `pytest tests/test_bootstrap.py::test_apply_update_set_importer_records_rejects_definition_response_subclass tests/test_bootstrap.py::test_apply_update_set_importer_records_rejects_operation_response_subclass -q` failed before implementation because unsafe response `.get()` hooks executed.
- `pytest tests/test_bootstrap.py::test_apply_update_set_importer_records_rejects_definition_response_subclass tests/test_bootstrap.py::test_apply_update_set_importer_records_rejects_operation_response_subclass tests/test_bootstrap.py::test_apply_update_set_importer_records_upserts_definition_then_operation tests/test_bootstrap.py::test_apply_update_set_importer_records_rejects_non_json_definition_lookup tests/test_bootstrap.py::test_apply_update_set_importer_records_rejects_non_json_operation_result -q` - 5 passed.
