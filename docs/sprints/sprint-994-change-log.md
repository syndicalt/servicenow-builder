# Sprint 994 Change Log - Runtime split-client story mutation response guard

## Summary

Hardened `SplitServiceNowClient` so PM story mutation responses are validated at the runtime routing boundary before notifiers, writeback callers, or CLI orchestration receive them.

## Security

`SplitServiceNowClient.update_story_fields()` now routes PM-client responses through `_split_story_mutation_result()`. The helper accepts only exact Python dictionaries and fails closed with `story mutation result is unsafe`.

Malformed story update response objects fail before downstream truthiness hooks, length hooks, response-field reads, audit decisions, or notifier completion logic can consume caller-controlled response behavior.

## Tests

- Added 1 failing-first story update response subclass assertion: `test_split_servicenow_client_rejects_story_update_response_subclass_without_leak`.
- Added 1 alternate story update response assertion: `test_split_servicenow_client_rejects_alternate_story_update_response`.
- Added 1 documentation assertion: `test_sprint_994_documents_runtime_split_client_story_mutation_response_guard`.

## Verification

- `pytest tests/test_runtime.py::test_split_servicenow_client_rejects_story_update_response_subclass_without_leak tests/test_runtime.py::test_split_servicenow_client_rejects_alternate_story_update_response -q` failed before implementation because `SplitServiceNowClient` returned unsafe story mutation response objects unchanged.
- `pytest tests/test_runtime.py::test_split_servicenow_client_rejects_story_update_response_subclass_without_leak tests/test_runtime.py::test_split_servicenow_client_rejects_alternate_story_update_response tests/test_runtime.py::test_split_servicenow_client_routes_story_and_development_operations -q` - 3 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_servicenow.py tests/test_runtime.py` - passed.
- `python3 -m mypy src/jedi_devproject/runtime_servicenow.py tests/test_runtime.py` - passed.
