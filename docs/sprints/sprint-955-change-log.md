# Sprint 955 Change Log - Retrieved Update Set handoff candidate truthiness guard

## Scope

- Hardened `_first_present()` so dictionary/form retrieved Update Set handoff does not use generic truthiness on candidate-derived fields before validation.
- Added `_candidate_field_present()` to make fallback selection decisions only for exact strings, booleans, integers, and nulls.
- Documented the candidate-field truthiness boundary in the operator guide.

## Production Hardening

- Unsupported candidate field objects now fail with `dictionary/form handoff field contains non-JSON value` before `__bool__`, `str()`, or `repr()` can execute.
- Dictionary/form handoff no longer allows model/provider-derived Python objects to run caller-controlled truthiness while choosing field aliases such as `element`, `field_name`, `column_label`, or `label`.
- Existing exact JSON scalar fallback behavior is preserved for supported candidate fields.

## Tests

- Added `test_create_update_set_handoff_rejects_truthy_object_field_without_leak`.
- Captured 1 failing-first retrieved Update Set handoff candidate truthiness assertion.
- Focused verification passed: 3 tests.
- Scoped verification passed: `tests/test_update_set_handoff.py` 33 tests and `tests/test_project_docs.py` 1028 tests.
- Static verification passed: `python3 -m ruff check src tests` and `python3 -m mypy src tests`.
- Full coverage verification passed: 3635 tests at 93.29% coverage.
