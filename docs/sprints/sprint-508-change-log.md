# Sprint 508 Change Log

## Business Rule generation field non-JSON value rejection

Hardened Business Rule customer-update generation so raw executable server-side candidate fields are not implicitly stringified before operation inference, script safety scanning, field-write validation, or XML generation.

`business_rule_customer_updates()` now rejects unsupported objects, bytes, containers in scalar positions, floats, and non-scalar values in target table, rule name, timing, operation aliases, filter conditions, script body, and declared table/field access metadata with the fixed `Business Rule generation field contains non-JSON value` diagnostic. The diagnostic does not echo field names, object type names, object string output, credential-like keys, generated script bodies, filter conditions, or access metadata.

This preserves valid Business Rule behavior, including operation inference from action aliases and field-write inference from valid scripts, while closing the boundary before operation inference, script safety scanning, field-write validation, XML generation, ServiceNow import, or story writeback.

## Verification

- Added 1 failing-first Business Rule generation test proving a secret-bearing Business Rule field object was previously stringified before validation.
- `python3 -m pytest tests/test_generation_validators.py::test_business_rule_customer_updates_rejects_non_json_field_without_leak -q`: failed before implementation because the strict diagnostic did not exist.
- `python3 -m pytest tests/test_generation_validators.py::test_business_rule_customer_updates_rejects_non_json_field_without_leak -q`: 1 test passed.
- `python3 -m pytest tests/test_generation_validators.py -q`: 54 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 582 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2463 total tests passed at 93.61% coverage.
