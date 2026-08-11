# Sprint 979 Change Log - Retrieved Update Set handoff change fields guard

## Summary

Hardened retrieved Update Set handoff change field handling so corrupted candidate change `fields` containers cannot execute truthiness, iteration, or mapping hooks while the handoff description or dictionary/form intent is prepared.

`_change_summary_lines()` and `_dictionary_form_intent()` now route candidate change fields through `_handoff_change_fields()`. The helper accepts only exact Python dictionaries whose keys are exact Python strings and fails closed with `retrieved Update Set handoff change fields contain non-JSON value`.

## Security impact

- Malformed change field containers fail before truthiness checks, `.items()`, `.get()`, `dict()`, proposed-change summary rendering, dictionary/form intent extraction, customer-update generation, ServiceNow import, story writeback, or returned handoff metadata.
- Malformed change field keys fail before summary-key rendering or intent extraction.
- Diagnostics do not include dictionary-subclass type names, custom hook output, field-key object output, or credential-like fragments.

## Tests

- Added 1 failing-first retrieved Update Set change fields container assertion: `test_create_update_set_handoff_rejects_change_fields_dict_subclass_without_leak`.
- Added 1 retrieved Update Set change field key assertion: `test_create_update_set_handoff_rejects_change_field_key_string_subclass_without_leak`.
- Added 1 project-doc assertion: `tests/test_project_docs.py::test_sprint_979_documents_handoff_change_fields_guard`.

## Verification

- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_change_fields_dict_subclass_without_leak -q` failed before implementation because a malformed fields dictionary subclass executed `__bool__` during handoff description rendering.
- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_change_fields_dict_subclass_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_change_field_key_string_subclass_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_change_table_string_subclass_without_leak -q` - 3 passed.
- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_change_fields_dict_subclass_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_change_field_key_string_subclass_without_leak tests/test_project_docs.py::test_sprint_979_documents_handoff_change_fields_guard -q` - 3 passed.
- `pytest tests/test_update_set_handoff.py -q` - 52 passed.
- `pytest tests/test_project_docs.py -q` - 1052 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` - 3690 passed, 93.25% coverage.
