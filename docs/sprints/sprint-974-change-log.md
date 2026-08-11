# Sprint 974 Change Log - Update Set apply change fields container guard

## Summary

Hardened direct Update Set apply candidate change field handling so corrupted in-process `CandidateChange.fields` containers cannot execute mapping hooks before dictionary normalization, form planning, XML attribute parsing, or dictionary upsert payload construction.

`apply_candidate_to_update_set()` now routes change field containers through `_apply_change_fields()` before helpers read `.get()`, iterate `.items()`, copy aliases, or construct ServiceNow payloads. The helper accepts only exact Python dictionaries. Dict subclasses and mapping-like objects fail closed with `Update Set apply change fields contain non-JSON value`.

## Security impact

- Malformed dictionary change field containers fail before `dict()`, alias copying, required-field checks, integration-user lookup, current Update Set preference writes, dictionary upsert, customer-update fetch, or apply result reporting.
- Malformed form change field containers fail before `.get()`, XML attribute parsing, section lookup, integration-user lookup, current Update Set preference writes, form upsert, customer-update fetch, or apply result reporting.
- Valid exact-dictionary change fields continue to use the existing scalar candidate field guards.

## Tests

- Added 2 failing-first direct Update Set apply change field container assertions: `test_apply_candidate_rejects_dictionary_change_fields_subclass_without_leak` and `test_apply_candidate_rejects_form_change_fields_subclass_without_leak`.
- Added 1 project-doc assertion: `tests/test_project_docs.py::test_sprint_974_documents_update_set_apply_change_fields_guard`.

## Verification

- `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_dictionary_change_fields_subclass_without_leak tests/test_update_set_apply.py::test_apply_candidate_rejects_form_change_fields_subclass_without_leak -q` failed before implementation because the change-fields diagnostic did not exist.
- `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_dictionary_change_fields_subclass_without_leak tests/test_update_set_apply.py::test_apply_candidate_rejects_form_change_fields_subclass_without_leak tests/test_update_set_apply.py::test_apply_candidate_sets_current_update_set_then_applies_dictionary_change tests/test_update_set_apply.py::test_apply_candidate_uses_named_form_section_when_provided -q` - 4 passed.
- `pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_dictionary_change_fields_subclass_without_leak tests/test_update_set_apply.py::test_apply_candidate_rejects_form_change_fields_subclass_without_leak tests/test_update_set_apply.py::test_apply_candidate_sets_current_update_set_then_applies_dictionary_change tests/test_update_set_apply.py::test_apply_candidate_uses_named_form_section_when_provided tests/test_project_docs.py::test_sprint_974_documents_update_set_apply_change_fields_guard -q` - 5 passed.
- `pytest tests/test_update_set_apply.py -q` - 39 passed.
- `pytest tests/test_project_docs.py -q` - 1047 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` - 3677 passed, total coverage 93.24%.
