# Sprint 513 Change Log

## Advisory ATF test plan generation field non-JSON value rejection

Sprint 513 continued production hardening by tightening advisory ATF test plan generation. ATF plans are review artifacts derived from candidate changes; they should never stringify arbitrary model, context, or stored-artifact objects into proposed test names, step descriptions, step inputs, not-covered details, assumptions, or durable artifact payloads.

`generate_atf_test_plan()` now rejects unsupported objects, bytes, containers in scalar positions, floats, and non-scalar values in candidate-derived table names, field names, policy names, catalog item names, variable names, conditions, operation flags, and declared field-write metadata with the fixed `ATF test plan generation field contains non-JSON value` diagnostic. The diagnostic does not echo object type names, object string output, credential-like keys, field values, policy names, catalog variables, conditions, or generated ATF artifact text.

This keeps the advisory ATF plan path aligned with the hardened customer-update generation paths: unsupported scalar input fails before test names, step descriptions, step inputs, not-covered entries, assumptions, or artifact payloads are built.

Verification:

- Added 1 failing-first ATF test plan generation test covering a secret-bearing object with a hostile `__str__`.
- `python3 -m pytest tests/test_atf_test_generation.py::test_atf_test_plan_rejects_non_json_candidate_field_without_leak -q`: failed before implementation because the strict diagnostic did not exist.
- `python3 -m pytest tests/test_atf_test_generation.py::test_atf_test_plan_rejects_non_json_candidate_field_without_leak -q`: 1 test passed.
- `python3 -m pytest tests/test_atf_test_generation.py -q`: 30 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 587 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2473 total tests passed at 93.52% coverage.
