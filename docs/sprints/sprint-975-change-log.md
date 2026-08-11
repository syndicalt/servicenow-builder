# Sprint 975 Change Log - Update Set apply change field key guard

## Summary

Hardened direct Update Set apply candidate change field keys so corrupted in-process `CandidateChange.fields` dictionaries cannot carry malformed keys into dictionary normalization, form planning, XML attribute parsing, or ServiceNow payload construction.

`_apply_change_fields()` now accepts only exact Python dictionaries whose keys are exact Python strings. Non-string keys and string-subclass keys fail closed with `Update Set apply change fields contain non-JSON value`.

## Security impact

- Malformed dictionary change field keys fail before alias copying, required-field checks, integration-user lookup, current Update Set preference writes, dictionary upsert payload construction, customer-update fetch, or apply result reporting.
- Malformed form change field keys fail before `.get()`, XML attribute parsing, section lookup, integration-user lookup, current Update Set preference writes, form upserts, customer-update fetch, or apply result reporting.
- Valid exact-string field keys continue to use the existing candidate scalar value guards.

## Tests

- Added 2 failing-first direct Update Set apply field-key assertions: `test_apply_candidate_rejects_dictionary_change_field_key_object_without_leak` and `test_apply_candidate_rejects_form_change_field_key_string_subclass`.
- Added 1 project-doc assertion: `tests/test_project_docs.py::test_sprint_975_documents_update_set_apply_change_field_key_guard`.

## Verification

- `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_dictionary_change_field_key_object_without_leak tests/test_update_set_apply.py::test_apply_candidate_rejects_form_change_field_key_string_subclass -q` failed before implementation because malformed field keys were accepted.
- `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_dictionary_change_field_key_object_without_leak tests/test_update_set_apply.py::test_apply_candidate_rejects_form_change_field_key_string_subclass tests/test_update_set_apply.py::test_apply_candidate_sets_current_update_set_then_applies_dictionary_change tests/test_update_set_apply.py::test_apply_candidate_uses_named_form_section_when_provided -q` - 4 passed.
- `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_dictionary_change_field_key_object_without_leak tests/test_update_set_apply.py::test_apply_candidate_rejects_form_change_field_key_string_subclass tests/test_update_set_apply.py::test_apply_candidate_sets_current_update_set_then_applies_dictionary_change tests/test_update_set_apply.py::test_apply_candidate_uses_named_form_section_when_provided tests/test_project_docs.py::test_sprint_975_documents_update_set_apply_change_field_key_guard -q` - 5 passed.
- `pytest tests/test_update_set_apply.py -q` - 41 passed.
- `pytest tests/test_project_docs.py -q` - 1048 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` - 3680 passed, total coverage 93.25%.
