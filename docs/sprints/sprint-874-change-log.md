# Sprint 874 Change Log

## Update Set apply form-section sys_id guard

- Added 1 failing-first Update Set apply missing section sys_id assertion: `test_apply_candidate_rejects_named_form_section_missing_sys_id`.
- Direct Update Set apply form layout planning now rejects matched `sys_ui_section` records without `sys_id` before form element lookup or upsert.

## Verification

- Focused import red: `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_named_form_section_missing_sys_id tests/test_project_docs.py::test_sprint_874_documents_update_set_apply_form_section_sys_id_guard -q` first failed because the new diagnostic constant did not exist.
- Focused behavioral red: `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_named_form_section_missing_sys_id tests/test_project_docs.py::test_sprint_874_documents_update_set_apply_form_section_sys_id_guard -q` then failed because the matched named section without `sys_id` did not raise `ValueError`.
- Focused green: `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_named_form_section_missing_sys_id tests/test_project_docs.py::test_sprint_874_documents_update_set_apply_form_section_sys_id_guard -q` passed with 2 tests.
- Update Set apply suite: `pytest tests/test_update_set_apply.py -q` passed with 13 tests.
- Docs suite: `pytest tests/test_project_docs.py -q` passed with 947 tests.
- Full gate: `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` passed with 3451 tests and 93.54% total coverage.
