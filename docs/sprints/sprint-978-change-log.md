# Sprint 978 Change Log - Retrieved Update Set handoff change identifier guard

## Summary

Hardened retrieved Update Set handoff change identifier handling so corrupted candidate change `table` or `operation` values cannot execute custom string hooks while the handoff description or builder routing is prepared.

`_customer_updates_for_candidate()`, `_dictionary_form_intent()`, and `_change_summary_lines()` now route candidate change identifiers through `_handoff_change_identifier_text()`. The helper accepts only exact Python strings and fails closed with `retrieved Update Set handoff changes contain non-JSON value`.

## Security impact

- Malformed change table values fail before proposed-change description rendering, table set construction, deterministic builder selection, dictionary/form intent resolution, XML generation, ServiceNow import, story writeback, or returned handoff metadata.
- Malformed change operation values fail before proposed-change description rendering or string interpolation.
- Diagnostics do not include string-subclass type names, custom string-hook output, sort-hook output, or credential-like fragments.

## Tests

- Added 1 failing-first retrieved Update Set change table identifier assertion: `test_create_update_set_handoff_rejects_change_table_string_subclass_without_leak`.
- Added 1 retrieved Update Set change operation identifier assertion: `test_create_update_set_handoff_rejects_change_operation_string_subclass_without_leak`.
- Added 1 project-doc assertion: `tests/test_project_docs.py::test_sprint_978_documents_handoff_change_identifier_guard`.

## Verification

- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_change_table_string_subclass_without_leak -q` failed before implementation because a malformed table string subclass executed `__str__` during handoff description rendering.
- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_change_table_string_subclass_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_change_operation_string_subclass_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_generated_customer_update_collection_subclass -q` - 3 passed.
- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_change_table_string_subclass_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_change_operation_string_subclass_without_leak tests/test_project_docs.py::test_sprint_978_documents_handoff_change_identifier_guard -q` - 3 passed.
- `pytest tests/test_update_set_handoff.py -q` - 50 passed.
- `pytest tests/test_project_docs.py -q` - 1051 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` - 3687 passed, 93.25% coverage.
