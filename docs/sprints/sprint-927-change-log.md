# Sprint 927 Change Log - Dictionary/form metadata scalar-subclass guard

## Scope

- Hardened `_metadata_text()` for dictionary/form live metadata values.
- Added a failing-first regression for hostile scalar-subclass `sys_ui_element` metadata.
- Documented the exact JSON scalar boundary for dictionary/form metadata consumption.

## Production Hardening

- `dictionary_form_customer_updates()` accepts exact strings, exact booleans, exact integers, and nulls for live metadata scalar values fetched from ServiceNow.
- Boolean and integer subclasses are rejected with the fixed `dictionary/form metadata field contains non-JSON value` diagnostic before string conversion.
- The dictionary/form metadata path does not call caller-controlled `__str__` methods on scalar subclasses while filtering default views, matching anchors, normalizing positions, planning form layout XML, importing retrieved Update Sets, or writing story diagnostics.

## Tests

- Added `test_generic_dictionary_form_rejects_scalar_subclass_metadata_without_leak`.
- Added `test_sprint_927_documents_dictionary_form_metadata_scalar_subclass_guard`.
- Captured 1 failing-first dictionary/form metadata scalar-subclass assertion.
- Focused sprint tests passed: 2 tests.
- Dictionary/form tests passed: 9 tests.
- Project documentation tests passed: 1000 tests.
- Static checks passed: `python3 -m ruff check src tests` and `python3 -m mypy src tests`.
- Full coverage passed: 3564 tests at 93.53% total coverage.
