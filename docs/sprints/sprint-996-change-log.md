# Sprint 996 Change Log - Bootstrap apply response guard

## Summary

Hardened bootstrap apply so ServiceNow mutation responses are validated before bootstrap result recording.

## Security

`apply_bootstrap_fields()` now routes dictionary field creation responses through `_bootstrap_create_field_result()` and table upsert responses through `_bootstrap_table_upsert_result()`.

`apply_platform_readonly_policy()` also validates the `sys_ui_policy` upsert response through `_bootstrap_table_upsert_result()`.

Create-field response subclasses fail closed with `bootstrap create field result is unsafe`. Table upsert response subclasses fail closed with `bootstrap table upsert result is unsafe`.

Malformed mutation response objects fail before truthiness hooks, length hooks, created-field recording, writable-field recording, platform-read-only result recording, or bootstrap apply result construction can consume caller-controlled behavior.

## Tests

- Added 1 failing-first bootstrap create-field response subclass assertion: `test_apply_bootstrap_fields_rejects_create_field_response_subclass_without_leak`.
- Added 1 failing-first bootstrap dictionary-upsert response subclass assertion: `test_apply_bootstrap_fields_rejects_dictionary_upsert_response_subclass_without_leak`.
- Added 1 failing-first bootstrap platform-policy response subclass assertion: `test_apply_bootstrap_fields_rejects_platform_policy_response_subclass_without_leak`.
- Added 1 documentation assertion: `test_sprint_996_documents_bootstrap_apply_response_guard`.

## Verification

- `pytest tests/test_bootstrap.py::test_apply_bootstrap_fields_rejects_create_field_response_subclass_without_leak tests/test_bootstrap.py::test_apply_bootstrap_fields_rejects_dictionary_upsert_response_subclass_without_leak tests/test_bootstrap.py::test_apply_bootstrap_fields_rejects_platform_policy_response_subclass_without_leak -q` failed before implementation because unsafe response subclasses were accepted.
- `pytest tests/test_bootstrap.py::test_apply_bootstrap_fields_rejects_create_field_response_subclass_without_leak tests/test_bootstrap.py::test_apply_bootstrap_fields_rejects_dictionary_upsert_response_subclass_without_leak tests/test_bootstrap.py::test_apply_bootstrap_fields_rejects_platform_policy_response_subclass_without_leak tests/test_bootstrap.py::test_apply_bootstrap_fields_creates_only_missing_custom_fields tests/test_bootstrap.py::test_apply_bootstrap_fields_adds_platform_readonly_policy -q` - 5 passed.
