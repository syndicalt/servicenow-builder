# Sprint 900 Change Log

## Advisory ATF test plan generation string-subclass guard

Hardened advisory ATF test plan generation so candidate-derived table names, field names, policy names, catalog item names, variable names, conditions, operation flags, and declared field-write metadata must use exact JSON-style scalar strings instead of string subclasses.

`generate_atf_test_plan()` now rejects string subclasses with the fixed `ATF test plan generation field contains non-JSON value` diagnostic. The diagnostic does not echo subclass names, overridden string method output, credential-like fragments, field values, policy names, catalog variables, conditions, or generated ATF artifact text.

This keeps the boundary closed before operation-flag parsing, scenario detection, step normalization, DTO validation, artifact serialization, ServiceNow import planning, or story writeback can execute caller-controlled string methods.

## Tests

- Added 1 failing-first ATF test plan string-subclass assertion: `test_atf_test_plan_rejects_string_subclass_candidate_field_without_leak`.
- Focused red: `pytest tests/test_atf_test_generation.py::test_atf_test_plan_rejects_string_subclass_candidate_field_without_leak tests/test_project_docs.py::test_sprint_900_documents_atf_generation_string_subclass_guard -q` failed because the string subclass executed its overridden `strip()` method during operation-flag parsing.
- Focused green: `pytest tests/test_atf_test_generation.py::test_atf_test_plan_rejects_string_subclass_candidate_field_without_leak tests/test_project_docs.py::test_sprint_900_documents_atf_generation_string_subclass_guard -q` passed with 2 tests.
- ATF test generation suite: `pytest tests/test_atf_test_generation.py -q` passed with 31 tests.
- Documentation suite: `pytest tests/test_project_docs.py -q` passed with 973 tests.
- Static gates: `python3 -m ruff check src tests` and `python3 -m mypy src tests` passed.
- Full coverage gate: `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` passed with 3510 tests at 93.52% coverage.
