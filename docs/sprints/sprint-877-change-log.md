# Sprint 877 Change Log

## Update Set apply invalid position guard

- Added 1 failing-first Update Set apply invalid position assertion: `test_apply_candidate_rejects_form_element_invalid_position_without_leak`.
- Direct Update Set apply form element position parsing now rejects malformed primitive position values with a stable diagnostic before insertion-position planning or upsert.

## Verification

- Focused import red: `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_form_element_invalid_position_without_leak tests/test_project_docs.py::test_sprint_877_documents_update_set_apply_invalid_position_guard -q` first failed because the new diagnostic constant did not exist.
- Focused behavioral red: `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_form_element_invalid_position_without_leak tests/test_project_docs.py::test_sprint_877_documents_update_set_apply_invalid_position_guard -q` then failed because Python integer parsing echoed the rejected primitive position value.
- Focused green: `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_form_element_invalid_position_without_leak tests/test_project_docs.py::test_sprint_877_documents_update_set_apply_invalid_position_guard -q` passed with 2 tests.
- Update Set apply suite: `pytest tests/test_update_set_apply.py -q` passed with 16 tests.
- Docs suite: `pytest tests/test_project_docs.py -q` passed with 950 tests.
- Full gate: `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` passed with 3457 tests and 93.54% total coverage.
