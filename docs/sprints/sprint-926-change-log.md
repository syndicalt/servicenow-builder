# Sprint 926 Change Log - Form-section generation scalar-subclass guard

## Scope

- Hardened `_form_section_field_text()` for form-section removal candidate and metadata values.
- Added a failing-first regression for hostile scalar-subclass form-section fields.
- Documented the exact JSON scalar boundary for form-section removal customer-update generation.

## Production Hardening

- `form_section_customer_updates()` accepts exact strings, exact booleans, exact integers, and nulls for scalar form-section values.
- Boolean and integer subclasses are rejected with the fixed `form section removal field contains non-JSON value` diagnostic before string conversion.
- The form-section path does not call caller-controlled `__str__` methods on scalar subclasses while parsing requested sections, normalizing views, matching sections, building DELETE XML, importing retrieved Update Sets, or writing story diagnostics.

## Tests

- Added `test_form_section_customer_updates_rejects_scalar_subclass_field_without_leak`.
- Added `test_sprint_926_documents_form_section_generation_scalar_subclass_guard`.
- Captured 1 failing-first form-section scalar-subclass assertion.
- Focused sprint tests passed: 2 tests.
- Update Set handoff tests passed: 29 tests.
- Project documentation tests passed: 999 tests.
- Static checks passed: `python3 -m ruff check src tests` and `python3 -m mypy src tests`.
- Full coverage passed: 3562 tests at 93.53% total coverage.
