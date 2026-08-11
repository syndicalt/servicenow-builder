# Sprint 970 Change Log - Update Set apply change identifier guard

## Summary

Hardened direct Update Set apply change routing so corrupted in-process `CandidateChange.table` and `CandidateChange.operation` values cannot reach table routing, operation checks, ServiceNow lookups, or mutation payloads.

`apply_candidate_to_update_set()` now routes change table and operation identifiers through `_apply_change_identifier_text()`. The helper accepts only exact Python strings. Non-string values and string subclasses fail closed with `Update Set apply change identifier contains non-JSON value`.

## Security impact

- Malformed change table values fail before supported-table routing, candidate field normalization, integration-user lookup, current Update Set preference writes, dictionary/form upserts, customer-update fetch, or apply result reporting.
- Malformed change operation values fail before operation support checks, candidate field normalization, integration-user lookup, current Update Set preference writes, dictionary/form upserts, customer-update fetch, or apply result reporting.
- Unsupported exact-string tables and operations continue to use their existing explicit unsupported-capability diagnostics.

## Tests

- Added 2 failing-first direct Update Set apply change identifier assertions: `test_apply_candidate_rejects_change_table_string_subclass` and `test_apply_candidate_rejects_change_operation_string_subclass`.
- Added 1 project-doc assertion: `tests/test_project_docs.py::test_sprint_970_documents_update_set_apply_change_identifier_guard`.

## Verification

- `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_change_table_string_subclass tests/test_update_set_apply.py::test_apply_candidate_rejects_change_operation_string_subclass -q` failed before implementation because the change-identifier diagnostic did not exist.
- `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_change_table_string_subclass tests/test_update_set_apply.py::test_apply_candidate_rejects_change_operation_string_subclass tests/test_update_set_apply.py::test_apply_candidate_sets_current_update_set_then_applies_dictionary_change -q` - 3 passed.
- `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_change_table_string_subclass tests/test_update_set_apply.py::test_apply_candidate_rejects_change_operation_string_subclass tests/test_update_set_apply.py::test_apply_candidate_sets_current_update_set_then_applies_dictionary_change tests/test_project_docs.py::test_sprint_970_documents_update_set_apply_change_identifier_guard -q` - 4 passed.
- `pytest tests/test_update_set_apply.py -q` - 32 passed.
- `pytest tests/test_project_docs.py -q` - 1043 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` - 3666 passed, total coverage 93.24%.
