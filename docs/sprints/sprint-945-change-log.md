# Sprint 945 Change Log - ATF generation list-subclass guard

## Scope

- Hardened `_atf_string_list()` so advisory ATF test plan generation accepts only exact lists before declared field-write metadata iteration.
- Documented the ATF list-subclass boundary in the operator guide.

## Production Hardening

- List subclasses now fail with `ATF test plan generation field contains non-JSON value` before iteration.
- ATF test plan generation no longer allows caller-controlled list iterators to run while deriving business-rule field-write scenarios.
- Exact list inputs remain supported for declared field-write metadata.

## Tests

- Added `test_atf_test_plan_rejects_list_subclass_candidate_field_without_leak`.
- Captured 1 failing-first ATF list-subclass iteration assertion.
- Focused verification passed: 2 tests.
- Scoped verification passed: `tests/test_atf_test_generation.py` 33 tests and `tests/test_project_docs.py` 1018 tests.
- Static verification passed: `python3 -m ruff check src tests` and `python3 -m mypy src tests`.
- Full coverage verification passed: 3613 tests at 93.25% coverage.
