# Sprint 971 Change Log - Update Set apply records collection guard

## Summary

Hardened direct Update Set apply ServiceNow record collection handling so malformed `fetch_table_records()` responses cannot execute container hooks during form-layout planning or apply result reporting.

`apply_candidate_to_update_set()` now normalizes every direct apply `fetch_table_records()` result through `_apply_records()`. The helper accepts only exact Python lists containing exact Python dictionaries. Non-list collections, list subclasses, non-dictionary records, and dictionary subclasses fail closed with `Update Set apply records contain non-JSON value`.

## Security impact

- Malformed `sys_ui_section` record collections fail before section-count checks, section metadata reads, `sys_ui_element` lookup, integration-user lookup, current Update Set preference writes, form upserts, customer-update fetch, or apply result reporting.
- Malformed `sys_ui_element` record collections fail before description-position planning, shifted-element planning, integration-user lookup, current Update Set preference writes, form upserts, customer-update fetch, or apply result reporting.
- Malformed `sys_update_xml` customer-update collections fail before truthiness checks, length calculation, or apply result reporting can execute response-controlled hooks.
- Valid exact-list ServiceNow responses with exact dictionary records continue to use the existing metadata scalar guards.

## Tests

- Added 2 failing-first direct Update Set apply record collection assertions: `test_apply_candidate_rejects_section_records_collection_subclass_without_leak` and `test_apply_candidate_rejects_customer_updates_collection_subclass_without_leak`.
- Added 1 project-doc assertion: `tests/test_project_docs.py::test_sprint_971_documents_update_set_apply_records_collection_guard`.

## Verification

- `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_section_records_collection_subclass_without_leak tests/test_update_set_apply.py::test_apply_candidate_rejects_customer_updates_collection_subclass_without_leak -q` failed before implementation because the records diagnostic did not exist.
- `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_section_records_collection_subclass_without_leak tests/test_update_set_apply.py::test_apply_candidate_rejects_customer_updates_collection_subclass_without_leak tests/test_update_set_apply.py::test_apply_candidate_uses_named_form_section_when_provided tests/test_update_set_apply.py::test_apply_candidate_sets_current_update_set_then_applies_dictionary_change -q` - 4 passed.
- `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_section_records_collection_subclass_without_leak tests/test_update_set_apply.py::test_apply_candidate_rejects_customer_updates_collection_subclass_without_leak tests/test_update_set_apply.py::test_apply_candidate_uses_named_form_section_when_provided tests/test_update_set_apply.py::test_apply_candidate_sets_current_update_set_then_applies_dictionary_change tests/test_project_docs.py::test_sprint_971_documents_update_set_apply_records_collection_guard -q` - 5 passed.
- `pytest tests/test_update_set_apply.py -q` - 34 passed.
- `pytest tests/test_project_docs.py -q` - 1044 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` - 3669 passed, total coverage 93.23%.
