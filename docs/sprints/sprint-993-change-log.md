# Sprint 993 Change Log - Runtime split-client single-record response guard

## Summary

Hardened `SplitServiceNowClient` so development single-record and mutation responses are validated at the runtime routing boundary before update-set handoff, bootstrap, or import decision code receives them.

## Security

`SplitServiceNowClient.fetch_table_record()` now routes development-client responses through `_split_optional_table_record_result()`. The helper accepts only `None` or exact Python dictionaries and fails closed with `table record lookup result is unsafe`.

`SplitServiceNowClient.upsert_table_record()` now routes development-client responses through `_split_table_mutation_result()`. The helper accepts only exact Python dictionaries and fails closed with `table mutation result is unsafe`.

`SplitServiceNowClient.import_update_set_xml()` now routes development-client responses through `_split_update_set_import_result()`. The helper accepts only exact Python dictionaries and fails closed with `update set import result is unsafe`.

Malformed response objects fail before downstream truthiness hooks, length hooks, record-field reads, mutation-result reads, handoff decisions, or import-status decisions can consume caller-controlled response behavior.

## Tests

- Added 1 failing-first table-record subclass assertion: `test_split_servicenow_client_rejects_table_record_subclass_without_leak`.
- Added 1 failing-first upsert response subclass assertion: `test_split_servicenow_client_rejects_upsert_response_subclass_without_leak`.
- Added 1 failing-first update-set import response subclass assertion: `test_split_servicenow_client_rejects_update_set_import_response_subclass`.
- Added 1 documentation assertion: `test_sprint_993_documents_runtime_split_client_single_record_response_guard`.

## Verification

- `pytest tests/test_runtime.py::test_split_servicenow_client_rejects_table_record_subclass_without_leak tests/test_runtime.py::test_split_servicenow_client_rejects_upsert_response_subclass_without_leak tests/test_runtime.py::test_split_servicenow_client_rejects_update_set_import_response_subclass -q` failed before implementation because `SplitServiceNowClient` returned unsafe development-client response objects unchanged.
- `pytest tests/test_runtime.py::test_split_servicenow_client_rejects_table_record_subclass_without_leak tests/test_runtime.py::test_split_servicenow_client_rejects_upsert_response_subclass_without_leak tests/test_runtime.py::test_split_servicenow_client_rejects_update_set_import_response_subclass tests/test_runtime.py::test_split_servicenow_client_routes_story_and_development_operations -q` - 4 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_servicenow.py tests/test_runtime.py` - passed.
- `python3 -m mypy src/jedi_devproject/runtime_servicenow.py tests/test_runtime.py` - passed.
