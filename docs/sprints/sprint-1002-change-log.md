# Sprint 1002 Change Log - Dictionary/form metadata record collection guard

## Summary

Hardened generic dictionary/form customer-update generation so ServiceNow form-layout metadata discovery results are validated before section iteration, section filtering, element lookup, anchor matching, form-layout planning, or XML generation.

## Security

`_form_updates()` now routes `sys_ui_section` and `sys_ui_element` `fetch_table_records()` responses through `_dictionary_form_metadata_records()`.

The helper accepts only exact Python lists containing exact Python dictionaries and fails closed with `dictionary/form metadata field contains non-JSON value`.

Malformed metadata result containers fail before list iteration, record `.get()` hooks, default-view filtering, element matching, position normalization, form-layout XML generation, ServiceNow import, or story writeback can consume caller-controlled container behavior.

## Tests

- Added 1 failing-first dictionary/form metadata record collection subclass assertion: `test_generic_dictionary_form_rejects_metadata_record_collection_subclass_without_leak`.
- Added 1 failing-first dictionary/form metadata record subclass assertion: `test_generic_dictionary_form_rejects_metadata_record_subclass_without_leak`.
- Added 1 documentation assertion: `test_sprint_1002_documents_dictionary_form_metadata_record_collection_guard`.

## Verification

- `pytest tests/test_generic_dictionary_form.py::test_generic_dictionary_form_updates_incident_field_and_form -q` - 1 passed before changes.
- `pytest tests/test_generic_dictionary_form.py::test_generic_dictionary_form_rejects_metadata_record_collection_subclass_without_leak tests/test_generic_dictionary_form.py::test_generic_dictionary_form_rejects_metadata_record_subclass_without_leak -q` failed before implementation because unsafe list iteration and record `.get()` hooks executed.
- `pytest tests/test_generic_dictionary_form.py::test_generic_dictionary_form_rejects_metadata_record_collection_subclass_without_leak tests/test_generic_dictionary_form.py::test_generic_dictionary_form_rejects_metadata_record_subclass_without_leak tests/test_generic_dictionary_form.py::test_generic_dictionary_form_updates_incident_field_and_form -q` - 3 passed.
