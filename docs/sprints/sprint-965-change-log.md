# Sprint 965 Change Log - Retrieved Update Set handoff lookup collection guard

## Summary

Hardened retrieved Update Set post-import lookup handling so malformed ServiceNow client response collections cannot execute custom truthiness, indexing, or mapping hooks while extracting the imported `sys_remote_update_set.sys_id`.

`import_retrieved_update_set()` now routes lookup responses through `_imported_update_set_sys_id()`. The helper accepts only an exact Python `list` response and, when a record is present, an exact dictionary for the first record before reading `sys_id`. Malformed collections fail closed with `retrieved Update Set lookup contains non-JSON value`.

## Security impact

- Post-import lookup no longer calls `bool()` on client-controlled lookup collections.
- Post-import lookup no longer indexes list subclasses or alternate iterable objects.
- Post-import lookup no longer calls `.get()` on dictionary subclasses or malformed record objects.
- Empty exact lists still raise the existing `ServiceNow imported Update Set lookup did not include sys_id` diagnostic.

## Tests

- Added 1 failing-first retrieved Update Set handoff lookup collection assertion: `test_import_retrieved_update_set_rejects_lookup_collection_subclass_without_leak`.
- Added 1 project-doc assertion: `tests/test_project_docs.py::test_sprint_965_documents_handoff_lookup_collection_guard`.

## Verification

- `pytest tests/test_update_set_handoff.py::test_import_retrieved_update_set_rejects_lookup_collection_subclass_without_leak -q` failed before implementation because direct lookup handling executed the hostile lookup collection `__bool__`.
- `pytest tests/test_update_set_handoff.py::test_import_retrieved_update_set_rejects_lookup_collection_subclass_without_leak tests/test_update_set_handoff.py::test_import_retrieved_update_set_rejects_non_json_lookup_sys_id_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_imports_retrieved_update_set_and_links_story -q` - 3 passed.
- `pytest tests/test_update_set_handoff.py::test_import_retrieved_update_set_rejects_lookup_collection_subclass_without_leak tests/test_update_set_handoff.py::test_import_retrieved_update_set_rejects_non_json_lookup_sys_id_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_imports_retrieved_update_set_and_links_story tests/test_project_docs.py::test_sprint_965_documents_handoff_lookup_collection_guard -q` - 4 passed.
- `pytest tests/test_update_set_handoff.py -q` - 43 passed.
- `pytest tests/test_project_docs.py -q` - 1038 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed with no issues in 203 source files.
- `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` - 3655 passed, total coverage 93.23%.
