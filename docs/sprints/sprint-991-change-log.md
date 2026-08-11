# Sprint 991 Change Log - Runtime split-client table-record collection guard

## Summary

Hardened `SplitServiceNowClient` so development table-record collection results are validated at the runtime routing boundary before builders, discovery routines, or update-set handoff logic receive them.

## Security

`SplitServiceNowClient.fetch_table_records()` now routes development-client responses through `_split_table_record_lookup_results()`. The helper accepts only exact Python lists and fails closed with `table record lookup result is unsafe`.

Malformed table-record collections fail before downstream truthiness hooks, length hooks, table-record iteration, builder routing, update-set XML generation, or development-instance mutations can consume caller-controlled collection behavior. Individual table-record field validation remains owned by the downstream builders and ServiceNow client parsing surfaces that know the required record schema.

## Tests

- Added 1 failing-first table-record collection subclass assertion: `test_split_servicenow_client_rejects_table_record_collection_subclass_without_leak`.
- Added 1 alternate iterable table-record collection assertion: `test_split_servicenow_client_rejects_alternate_table_record_collection`.
- Added 1 documentation assertion: `test_sprint_991_documents_runtime_split_client_table_record_collection_guard`.

## Verification

- `pytest tests/test_runtime.py::test_split_servicenow_client_rejects_table_record_collection_subclass_without_leak tests/test_runtime.py::test_split_servicenow_client_rejects_alternate_table_record_collection -q` failed before implementation because `SplitServiceNowClient` returned unsafe table-record collections unchanged.
- `pytest tests/test_runtime.py::test_split_servicenow_client_rejects_table_record_collection_subclass_without_leak tests/test_runtime.py::test_split_servicenow_client_rejects_alternate_table_record_collection tests/test_runtime.py::test_split_servicenow_client_routes_story_and_development_operations -q` - 3 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_servicenow.py tests/test_runtime.py` - passed.
- `python3 -m mypy src/jedi_devproject/runtime_servicenow.py tests/test_runtime.py` - passed.
