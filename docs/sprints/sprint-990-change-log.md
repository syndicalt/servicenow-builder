# Sprint 990 Change Log - Runtime split-client story lookup guard

## Summary

Hardened `SplitServiceNowClient` so PM/story lookup results are validated at the runtime routing boundary before worker orchestration or CLI pipeline consumers receive them.

## Security

`SplitServiceNowClient.fetch_ready_stories()` and `SplitServiceNowClient.fetch_stories()` now route PM/story client responses through `_split_story_lookup_results()`. The helper accepts only exact Python lists and fails closed with `story lookup result is unsafe`.

Malformed story collections fail before downstream truthiness hooks, length hooks, worker scheduling, pipeline execution, or development-instance operations can consume caller-controlled collection behavior. The split client still leaves story item validation to the existing downstream surfaces that own item-specific requirements.

## Tests

- Added 1 failing-first ready-story collection assertion: `test_split_servicenow_client_rejects_ready_story_collection_subclass_without_leak`.
- Added 1 failing-first story lookup collection assertion: `test_split_servicenow_client_rejects_story_lookup_collection_subclass_without_leak`.
- Added 1 documentation assertion: `test_sprint_990_documents_runtime_split_client_story_lookup_guard`.

## Verification

- `pytest tests/test_runtime.py::test_split_servicenow_client_rejects_ready_story_collection_subclass_without_leak tests/test_runtime.py::test_split_servicenow_client_rejects_story_lookup_collection_subclass_without_leak -q` failed before implementation because `SplitServiceNowClient` returned list subclasses unchanged.
- `pytest tests/test_runtime.py::test_split_servicenow_client_rejects_ready_story_collection_subclass_without_leak tests/test_runtime.py::test_split_servicenow_client_rejects_story_lookup_collection_subclass_without_leak tests/test_runtime.py::test_split_servicenow_client_routes_story_and_development_operations -q` - 3 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_servicenow.py tests/test_runtime.py` - passed.
- `python3 -m mypy src/jedi_devproject/runtime_servicenow.py tests/test_runtime.py` - passed.
