# Sprint 953 Change Log - Dictionary/form reference dict-subclass guard

## Scope

- Hardened `_is_global_main_view_section()` so dictionary/form retrieved Update Set handoff accepts only exact dictionaries before section view `value` or `display_value` lookup.
- Hardened `_form_layout_payload()`, `_view_payload_value()`, and `reference_value()` so form-layout XML generation and metadata reference extraction accept only exact dictionaries before reference lookup.
- Documented the dictionary/form reference-dictionary subclass boundary in the operator guide.

## Production Hardening

- Dictionary subclasses now fail with `dictionary/form metadata field contains non-JSON value` before retrieved Update Set handoff planning.
- Dictionary/form handoff no longer allows caller-controlled dictionary accessors to run while filtering default sections, serializing view metadata, or extracting ServiceNow reference values.
- Exact JSON dictionaries remain supported for ServiceNow reference metadata returned by Table API lookups.

## Tests

- Added `test_generic_dictionary_form_rejects_view_dict_subclass_metadata_without_leak`.
- Captured 1 failing-first dictionary/form reference dict-subclass assertion.
- Focused verification passed: 2 tests.
- Scoped verification passed: `tests/test_generic_dictionary_form.py` 10 tests and `tests/test_project_docs.py` 1026 tests.
- Static verification passed: `python3 -m ruff check src tests` and `python3 -m mypy src tests`.
- Full coverage verification passed: 3631 tests at 93.30% coverage.
