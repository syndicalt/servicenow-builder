# Sprint 997 Change Log - Lifecycle webhook apply response guard

## Summary

Hardened lifecycle webhook bootstrap apply so ServiceNow upsert response containers are validated before response-field access.

## Security

`apply_lifecycle_webhook_records()` now routes `sys_rest_message`, `sys_rest_message_fn`, and `sys_script` upsert responses through `_lifecycle_webhook_upsert_result()`.

The helper accepts only exact Python dictionaries and fails closed with `Lifecycle webhook lookup contains non-JSON value`.

Malformed upsert response containers fail before `.get()` hooks, dependent REST method upserts, `sys_id` extraction, apply-result recording, object representations, bytes, containers, or credential-like response fragments can be consumed or exposed.

## Tests

- Added 1 failing-first lifecycle REST message response subclass assertion: `test_apply_lifecycle_webhook_records_rejects_rest_message_response_subclass`.
- Added 1 failing-first lifecycle REST method response subclass assertion: `test_apply_lifecycle_webhook_records_rejects_method_response_subclass_without_leak`.
- Added 1 documentation assertion: `test_sprint_997_documents_lifecycle_apply_response_guard`.

## Verification

- `pytest tests/test_bootstrap.py::test_apply_lifecycle_webhook_records_rejects_rest_message_response_subclass tests/test_bootstrap.py::test_apply_lifecycle_webhook_records_rejects_method_response_subclass_without_leak -q` failed before implementation because unsafe response `.get()` hooks executed.
- `pytest tests/test_bootstrap.py::test_apply_lifecycle_webhook_records_rejects_rest_message_response_subclass tests/test_bootstrap.py::test_apply_lifecycle_webhook_records_rejects_method_response_subclass_without_leak tests/test_bootstrap.py::test_apply_lifecycle_webhook_records_upserts_planned_records tests/test_bootstrap.py::test_apply_lifecycle_webhook_records_rejects_non_json_rest_message_lookup tests/test_bootstrap.py::test_apply_lifecycle_webhook_records_rejects_non_json_method_result -q` - 5 passed.
