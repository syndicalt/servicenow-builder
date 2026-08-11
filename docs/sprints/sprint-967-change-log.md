# Sprint 967 Change Log - Retrieved Update Set import metadata guard

## Summary

Hardened retrieved Update Set import metadata handling so malformed name, remote sys_id, or description values cannot execute custom string methods while unload XML is generated.

`import_retrieved_update_set()` now routes the retrieved Update Set name, `remote_sys_id`, and description through `_import_metadata_text()` before customer-update XML generation. The helper accepts only exact Python strings. Non-string values and string subclasses fail closed with `retrieved Update Set metadata contains non-JSON value`.

## Security impact

- Retrieved Update Set unload XML generation no longer passes string subclasses to `html.escape()`.
- Malformed import metadata fails before customer update XML generation, XML escaping, ServiceNow import, post-import lookup construction, story work-note formatting, or returned handoff metadata.
- The normal runtime handoff path remains unchanged because it already produces exact string metadata.

## Tests

- Added 1 failing-first retrieved Update Set import metadata assertion: `test_import_retrieved_update_set_rejects_metadata_string_subclass_without_leak`.
- Added 1 project-doc assertion: `tests/test_project_docs.py::test_sprint_967_documents_update_set_import_metadata_guard`.

## Verification

- `pytest tests/test_update_set_handoff.py::test_import_retrieved_update_set_rejects_metadata_string_subclass_without_leak -q` failed before implementation because XML generation passed the hostile string subclass to `html.escape()`.
- `pytest tests/test_update_set_handoff.py::test_import_retrieved_update_set_rejects_metadata_string_subclass_without_leak tests/test_update_set_handoff.py::test_import_retrieved_update_set_rejects_customer_update_collection_subclass tests/test_update_set_handoff.py::test_create_update_set_handoff_imports_retrieved_update_set_and_links_story -q` - 3 passed.
- `pytest tests/test_update_set_handoff.py::test_import_retrieved_update_set_rejects_metadata_string_subclass_without_leak tests/test_update_set_handoff.py::test_import_retrieved_update_set_rejects_customer_update_collection_subclass tests/test_update_set_handoff.py::test_create_update_set_handoff_imports_retrieved_update_set_and_links_story tests/test_project_docs.py::test_sprint_967_documents_update_set_import_metadata_guard -q` - 4 passed.
- `pytest tests/test_update_set_handoff.py -q` - 45 passed.
- `pytest tests/test_project_docs.py -q` - 1040 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed with no issues in 203 source files.
- `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` - 3659 passed, total coverage 93.23%.
