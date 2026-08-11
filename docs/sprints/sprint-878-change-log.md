# Sprint 878 Change Log

## Update Set apply section view metadata guard

- Added 1 failing-first Update Set apply section view metadata assertion: `test_apply_candidate_rejects_section_view_non_json_value_without_leak`.
- Direct Update Set apply section view filtering now rejects unsupported non-JSON view metadata values before default-view filtering, form element lookup, or upsert.

## Verification

- Focused red: `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_section_view_non_json_value_without_leak tests/test_project_docs.py::test_sprint_878_documents_update_set_apply_view_metadata_guard -q` failed before implementation because unsupported view metadata did not raise `ValueError`.
- Focused green: `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_section_view_non_json_value_without_leak tests/test_project_docs.py::test_sprint_878_documents_update_set_apply_view_metadata_guard -q` passed with 2 tests.
- Update Set apply suite: `pytest tests/test_update_set_apply.py -q` passed with 17 tests.
- Docs suite: `pytest tests/test_project_docs.py -q` passed with 951 tests.
- Full gate: `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` passed with 3459 tests and 93.54% total coverage.
