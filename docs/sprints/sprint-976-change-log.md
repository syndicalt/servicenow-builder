# Sprint 976 Change Log - Update Set apply dictionary discovery identifier guard

## Summary

Hardened direct Update Set apply custom dictionary discovery so corrupted in-process `CandidateChange.table` values cannot execute equality hooks before the existing table identifier guard runs.

`_custom_dictionary_elements()` now routes every candidate change table through `_apply_change_identifier_text()` before comparing it with `sys_dictionary`. The same fixed diagnostic used by table routing, `Update Set apply change identifier contains non-JSON value`, now covers pre-routing dictionary discovery.

## Security impact

- Malformed change table values fail before custom dictionary discovery comparisons, dictionary field normalization, form target inference, integration-user lookup, current Update Set preference writes, dictionary/form upserts, customer-update fetch, or apply result reporting.
- Existing exact-string table values continue through the same routing and operation guards.
- The direct apply path no longer has an earlier table-comparison path that can bypass the Sprint 970 identifier guard.

## Tests

- Added 1 failing-first direct Update Set apply dictionary discovery assertion: `test_apply_candidate_rejects_change_table_object_before_dictionary_discovery`.
- Added 1 project-doc assertion: `tests/test_project_docs.py::test_sprint_976_documents_update_set_apply_dictionary_discovery_identifier_guard`.

## Verification

- `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_change_table_object_before_dictionary_discovery -q` failed before implementation because a malformed table equality hook executed during custom dictionary discovery.
- `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_change_table_object_before_dictionary_discovery tests/test_update_set_apply.py::test_apply_candidate_rejects_change_table_string_subclass tests/test_update_set_apply.py::test_apply_candidate_rejects_change_operation_string_subclass tests/test_update_set_apply.py::test_apply_candidate_sets_current_update_set_then_applies_dictionary_change -q` - 4 passed.
- `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_change_table_object_before_dictionary_discovery tests/test_update_set_apply.py::test_apply_candidate_rejects_change_table_string_subclass tests/test_update_set_apply.py::test_apply_candidate_rejects_change_operation_string_subclass tests/test_update_set_apply.py::test_apply_candidate_sets_current_update_set_then_applies_dictionary_change tests/test_project_docs.py::test_sprint_976_documents_update_set_apply_dictionary_discovery_identifier_guard -q` - 5 passed.
- `pytest tests/test_update_set_apply.py -q` - 42 passed.
- `pytest tests/test_project_docs.py -q` - 1049 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` - 3682 passed, total coverage 93.25%.
