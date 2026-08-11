# Sprint 977 Change Log - Retrieved Update Set generated customer update guard

## Summary

Hardened retrieved Update Set handoff generated customer-update handling so malformed builder outputs cannot execute container hooks during the handoff emptiness check.

`_customer_updates_for_candidate()` now routes builder output through `_customer_updates()` before checking whether any customer updates were generated. The helper accepts only exact Python lists containing exact dictionaries and fails closed with `retrieved Update Set customer update contains non-JSON value`.

## Security impact

- Malformed dictionary/form or UI Policy builder output fails before truthiness checks, XML serialization, ServiceNow import, story writeback, or returned handoff metadata.
- The direct import boundary remains guarded by the same `_customer_updates()` helper before XML generation.
- Valid exact-list builder output continues to fail with the existing empty-update diagnostic when the list is exactly empty.

## Tests

- Added 1 failing-first retrieved Update Set generated customer-update assertion: `test_create_update_set_handoff_rejects_generated_customer_update_collection_subclass`.
- Added 1 project-doc assertion: `tests/test_project_docs.py::test_sprint_977_documents_handoff_generated_customer_update_guard`.

## Verification

- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_generated_customer_update_collection_subclass -q` failed before implementation because a malformed generated update collection executed `__bool__` before exact-shape validation.
- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_generated_customer_update_collection_subclass tests/test_update_set_handoff.py::test_create_update_set_handoff_imports_retrieved_update_set_and_links_story tests/test_update_set_handoff.py::test_import_retrieved_update_set_rejects_customer_update_collection_subclass -q` - 3 passed.
- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_generated_customer_update_collection_subclass tests/test_update_set_handoff.py::test_create_update_set_handoff_imports_retrieved_update_set_and_links_story tests/test_update_set_handoff.py::test_import_retrieved_update_set_rejects_customer_update_collection_subclass tests/test_project_docs.py::test_sprint_966_documents_customer_update_collection_guard tests/test_project_docs.py::test_sprint_977_documents_handoff_generated_customer_update_guard -q` - 5 passed.
- `pytest tests/test_update_set_handoff.py -q` - 48 passed.
- `pytest tests/test_project_docs.py -q` - 1050 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` - 3684 passed, 93.25% coverage.
