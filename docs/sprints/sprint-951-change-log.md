# Sprint 951 Change Log - Form-section container-subclass guard

## Scope

- Hardened `_section_names()` so form-section removal customer-update generation accepts only exact lists before requested section iteration.
- Hardened `_reference_display_or_value()` so discovered `sys_ui_section` reference metadata must be an exact dictionary before display/value lookup.
- Documented the form-section container-subclass boundary in the operator guide.

## Production Hardening

- List and dictionary subclasses now fail with `form section removal field contains non-JSON value` before form-section DELETE XML generation.
- Form-section generation no longer allows caller-controlled list iterators or dictionary accessors to run while parsing requested sections or discovered section metadata.
- Exact JSON list and dictionary inputs remain supported for requested section names and ServiceNow reference metadata.

## Tests

- Added `test_form_section_customer_updates_rejects_list_subclass_field_without_leak`.
- Added `test_form_section_customer_updates_rejects_dict_subclass_metadata_without_leak`.
- Captured 2 failing-first form-section container-subclass execution assertions.
- Focused verification passed: 3 tests.
- Scoped verification passed: `tests/test_update_set_handoff.py` 31 tests and `tests/test_project_docs.py` 1024 tests.
- Static verification passed: `python3 -m ruff check src tests` and `python3 -m mypy src tests`.
- Full coverage verification passed: 3627 tests at 93.28% coverage.
