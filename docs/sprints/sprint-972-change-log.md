# Sprint 972 Change Log - Update Set apply single-record lookup guard

## Summary

Hardened direct Update Set apply single-record lookup handling so malformed `fetch_table_record()` responses cannot execute mapping hooks while resolving the integration user.

`_integration_user_sys_id()` now normalizes the ServiceNow `sys_user` lookup response through `_apply_optional_record()` before reading `sys_id`. The helper accepts only `None` for a missing record or an exact Python dictionary for a found record. Mapping-like objects and dictionary subclasses fail closed with `Update Set apply record contains non-JSON value`.

## Security impact

- Malformed integration-user lookup records fail before `.get("sys_id")`, current Update Set preference writes, dictionary/form upserts, customer-update fetch, or apply result reporting.
- Missing integration users still use the existing not-found path and fail before mutation.
- Valid exact-dictionary ServiceNow lookup responses continue to use the existing primitive lookup scalar guard for `sys_id`.

## Tests

- Added 1 failing-first direct Update Set apply single-record assertion: `test_apply_candidate_rejects_integration_user_record_subclass_without_leak`.
- Added 1 project-doc assertion: `tests/test_project_docs.py::test_sprint_972_documents_update_set_apply_single_record_guard`.

## Verification

- `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_integration_user_record_subclass_without_leak -q` failed before implementation because the single-record diagnostic did not exist.
- `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_integration_user_record_subclass_without_leak tests/test_update_set_apply.py::test_apply_candidate_requires_integration_user_before_mutation tests/test_update_set_apply.py::test_apply_candidate_sets_current_update_set_then_applies_dictionary_change -q` - 3 passed.
- `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_integration_user_record_subclass_without_leak tests/test_update_set_apply.py::test_apply_candidate_requires_integration_user_before_mutation tests/test_update_set_apply.py::test_apply_candidate_sets_current_update_set_then_applies_dictionary_change tests/test_project_docs.py::test_sprint_972_documents_update_set_apply_single_record_guard -q` - 4 passed.
- `pytest tests/test_update_set_apply.py -q` - 35 passed.
- `pytest tests/test_project_docs.py -q` - 1045 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` - 3671 passed, total coverage 93.24%.
