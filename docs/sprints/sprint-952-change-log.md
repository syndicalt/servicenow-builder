# Sprint 952 Change Log - Update Set apply reference dict-subclass guard

## Scope

- Hardened `_is_global_main_story_view_section()` so direct Update Set apply accepts only exact dictionaries before section view `value` or `display_value` lookup.
- Hardened `_reference_value()` so direct apply metadata reference extraction accepts only exact dictionaries before `value` lookup.
- Documented the direct Update Set apply reference-dictionary subclass boundary in the operator guide.

## Production Hardening

- Dictionary subclasses now fail with `Update Set apply metadata contains non-JSON value` before direct form layout planning.
- Legacy direct apply no longer allows caller-controlled dictionary accessors to run while filtering default story sections or extracting ServiceNow reference metadata.
- Exact JSON dictionaries remain supported for ServiceNow reference metadata returned by Table API lookups.

## Tests

- Added `test_apply_candidate_rejects_section_view_dict_subclass_without_leak`.
- Captured 1 failing-first Update Set apply reference dict-subclass assertion.
- Focused verification passed: 3 tests.
- Scoped verification passed: `tests/test_update_set_apply.py` 30 tests and `tests/test_project_docs.py` 1025 tests.
- Static verification passed: `python3 -m ruff check src tests` and `python3 -m mypy src tests`.
- Full coverage verification passed: 3629 tests at 93.29% coverage.
