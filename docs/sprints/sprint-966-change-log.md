# Sprint 966 Change Log - Retrieved Update Set customer update collection guard

## Summary

Hardened retrieved Update Set customer-update XML generation so malformed generated update collections cannot execute custom iteration or mapping hooks before scalar validation.

`import_retrieved_update_set()` now routes generated customer updates through `_customer_updates()` before unload XML generation. The helper accepts only an exact Python `list` containing exact dictionaries. List subclasses, alternate iterables, dictionary subclasses, malformed update records, and corrupted builder fixtures fail closed with `retrieved Update Set customer update contains non-JSON value`.

## Security impact

- Retrieved Update Set XML generation no longer iterates untrusted customer-update collection subclasses.
- Retrieved Update Set XML generation no longer calls `.get()` on dictionary subclasses or malformed update records.
- Malformed customer-update collections fail before field extraction, CDATA escaping, XML assembly, ServiceNow import, or post-import lookup.

## Tests

- Added 1 failing-first retrieved Update Set customer update collection assertion: `test_import_retrieved_update_set_rejects_customer_update_collection_subclass`.
- Added 1 project-doc assertion: `tests/test_project_docs.py::test_sprint_966_documents_customer_update_collection_guard`.

## Verification

- `pytest tests/test_update_set_handoff.py::test_import_retrieved_update_set_rejects_customer_update_collection_subclass -q` failed before implementation because direct XML generation iterated the hostile customer-update collection.
- `pytest tests/test_update_set_handoff.py::test_import_retrieved_update_set_rejects_customer_update_collection_subclass tests/test_update_set_handoff.py::test_import_retrieved_update_set_rejects_non_json_customer_update_scalar_without_leak tests/test_update_set_handoff.py::test_import_retrieved_update_set_rejects_string_subclass_customer_update_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_imports_retrieved_update_set_and_links_story -q` - 4 passed.
- `pytest tests/test_update_set_handoff.py::test_import_retrieved_update_set_rejects_customer_update_collection_subclass tests/test_update_set_handoff.py::test_import_retrieved_update_set_rejects_non_json_customer_update_scalar_without_leak tests/test_update_set_handoff.py::test_import_retrieved_update_set_rejects_string_subclass_customer_update_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_imports_retrieved_update_set_and_links_story tests/test_project_docs.py::test_sprint_966_documents_customer_update_collection_guard -q` - 5 passed.
- `pytest tests/test_update_set_handoff.py -q` - 44 passed.
- `pytest tests/test_project_docs.py -q` - 1039 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed with no issues in 203 source files.
- `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` - 3657 passed, total coverage 93.22%.
