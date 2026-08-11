# Sprint 992 Change Log - Runtime split-client story metadata collection guard

## Summary

Hardened `SplitServiceNowClient` so PM story metadata collections are validated at the runtime routing boundary before writeback, bootstrap, or story metadata decision code receives them.

## Security

`SplitServiceNowClient.fetch_story_state_choices()` now routes PM-client responses through `_split_story_state_choice_results()` and fails closed with `story state choices result is unsafe` unless the response is an exact Python list.

`SplitServiceNowClient.fetch_story_dictionary_fields()` now routes PM-client responses through `_split_story_dictionary_field_results()` and fails closed with `story dictionary fields result is unsafe` unless the response is an exact Python list.

Malformed story metadata collections fail before downstream truthiness hooks, length hooks, state-choice iteration, dictionary-field iteration, writeback state mapping, bootstrap checks, or story metadata decisions can consume caller-controlled collection behavior. Individual choice and field DTO validation remains owned by the downstream surfaces that know the required item schema.

## Tests

- Added 1 failing-first state-choice collection subclass assertion: `test_split_servicenow_client_rejects_state_choice_collection_subclass_without_leak`.
- Added 1 failing-first dictionary-field collection subclass assertion: `test_split_servicenow_client_rejects_dictionary_field_collection_subclass`.
- Added 1 documentation assertion: `test_sprint_992_documents_runtime_split_client_story_metadata_collection_guard`.

## Verification

- `pytest tests/test_runtime.py::test_split_servicenow_client_rejects_state_choice_collection_subclass_without_leak tests/test_runtime.py::test_split_servicenow_client_rejects_dictionary_field_collection_subclass_without_leak -q` failed before implementation because `SplitServiceNowClient` returned unsafe PM story metadata collections unchanged.
- `pytest tests/test_runtime.py::test_split_servicenow_client_rejects_state_choice_collection_subclass_without_leak tests/test_runtime.py::test_split_servicenow_client_rejects_dictionary_field_collection_subclass tests/test_runtime.py::test_split_servicenow_client_routes_story_and_development_operations -q` - 3 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_servicenow.py tests/test_runtime.py` - passed.
- `python3 -m mypy src/jedi_devproject/runtime_servicenow.py tests/test_runtime.py` - passed.
