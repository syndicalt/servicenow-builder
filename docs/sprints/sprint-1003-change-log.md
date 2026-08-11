# Sprint 1003 Change Log - Form-section metadata record collection guard

## Summary

Hardened form-section removal customer-update generation so ServiceNow section metadata discovery results are validated before section iteration, view filtering, section matching, section sys_id resolution, or DELETE XML generation.

## Security

`form_section_customer_updates()` now routes `sys_ui_section` `fetch_table_records()` responses through `_form_section_metadata_records()`.

The helper accepts only exact Python lists containing exact Python dictionaries and fails closed with `form section removal field contains non-JSON value`.

Malformed metadata result containers fail before list iteration, record `.get()` hooks, view filtering, section matching, section sys_id resolution, form-section DELETE XML generation, ServiceNow import, or story writeback can consume caller-controlled container behavior.

## Tests

- Added 1 failing-first form-section metadata record collection subclass assertion: `test_form_section_customer_updates_rejects_metadata_collection_subclass_without_leak`.
- Added 1 failing-first form-section metadata record subclass assertion: `test_form_section_customer_updates_rejects_metadata_record_subclass_without_leak`.
- Added 1 documentation assertion: `test_sprint_1003_documents_form_section_metadata_record_collection_guard`.

## Verification

- `pytest tests/test_update_set_handoff.py::test_form_section_customer_updates_rejects_metadata_collection_subclass_without_leak tests/test_update_set_handoff.py::test_form_section_customer_updates_rejects_metadata_record_subclass_without_leak -q` failed before implementation because unsafe list iteration and record `.get()` hooks executed.
- `pytest tests/test_update_set_handoff.py::test_form_section_customer_updates_rejects_metadata_collection_subclass_without_leak tests/test_update_set_handoff.py::test_form_section_customer_updates_rejects_metadata_record_subclass_without_leak tests/test_update_set_handoff.py::test_form_section_customer_updates_respects_non_default_view -q` - 3 passed.
