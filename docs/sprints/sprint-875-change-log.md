# Sprint 875 Change Log

## Update Set apply metadata non-JSON guard

- Added 1 failing-first Update Set apply metadata non-JSON assertion: `test_apply_candidate_rejects_named_form_section_non_json_sys_id_without_leak`.
- Direct Update Set apply form metadata conversion now rejects unsupported non-JSON metadata values before form element lookup or upsert.

## Verification

- Focused import red: `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_named_form_section_non_json_sys_id_without_leak tests/test_project_docs.py::test_sprint_875_documents_update_set_apply_metadata_non_json_guard -q` first failed because the new diagnostic constant did not exist.
- Focused behavioral red: `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_named_form_section_non_json_sys_id_without_leak tests/test_project_docs.py::test_sprint_875_documents_update_set_apply_metadata_non_json_guard -q` then failed because the matched named section object `sys_id` did not raise `ValueError`.
- Focused green: `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_named_form_section_non_json_sys_id_without_leak tests/test_project_docs.py::test_sprint_875_documents_update_set_apply_metadata_non_json_guard -q` passed with 2 tests.
- Update Set apply suite: `pytest tests/test_update_set_apply.py -q` passed with 14 tests.
- Docs suite: `pytest tests/test_project_docs.py -q` passed with 948 tests.
- Full gate: `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` passed with 3453 tests and 93.53% total coverage.
