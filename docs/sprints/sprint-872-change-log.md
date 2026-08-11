# Sprint 872 Change Log

## Form-section missing sys_id guard

- Added 1 failing-first form-section missing sys_id assertion: `test_form_section_customer_updates_rejects_missing_section_sys_id`.
- Form-section removal customer-update generation now rejects matched `sys_ui_section` records without `sys_id` before update naming or DELETE XML generation.

## Verification

- Focused red: `pytest tests/test_update_set_handoff.py::test_form_section_customer_updates_rejects_missing_section_sys_id tests/test_project_docs.py::test_sprint_872_documents_form_section_missing_sys_id_guard -q` failed before implementation because the missing `sys_id` record did not raise `ValueError`.
- Focused green: `pytest tests/test_update_set_handoff.py::test_form_section_customer_updates_rejects_missing_section_sys_id tests/test_project_docs.py::test_sprint_872_documents_form_section_missing_sys_id_guard -q` passed with 2 tests.
- Handoff suite: `pytest tests/test_update_set_handoff.py -q` passed with 26 tests.
- Docs suite: `pytest tests/test_project_docs.py -q` passed with 945 tests.
- Full gate: `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` passed with 3447 tests and 93.53% total coverage.
