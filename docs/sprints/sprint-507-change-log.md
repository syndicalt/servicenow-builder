# Sprint 507 Change Log

## Script Include generation field non-JSON value rejection

Hardened Script Include customer-update generation so raw executable-code candidate fields are not implicitly stringified before script safety scanning, DTO validation, or XML generation.

`script_include_customer_updates()` now rejects unsupported objects, bytes, containers in scalar positions, floats, and non-scalar values in Script Include name, API name, scope, callable/active flags, description, script body, public methods, table access metadata, and field access metadata with the fixed `Script Include generation field contains non-JSON value` diagnostic. The diagnostic does not echo field names, object type names, object string output, credential-like keys, generated script bodies, method names, or access metadata.

This preserves valid Script Include behavior, including inferred public methods from valid script bodies, while closing the boundary before script safety scanning, DTO validation, XML generation, ServiceNow import, or story writeback.

## Verification

- Added 1 failing-first Script Include generation test proving a secret-bearing Script Include field object was previously stringified before validation.
- `python3 -m pytest tests/test_generation_validators.py::test_script_include_customer_updates_rejects_non_json_field_without_leak -q`: failed before implementation because the strict diagnostic did not exist.
- `python3 -m pytest tests/test_generation_validators.py::test_script_include_customer_updates_rejects_non_json_field_without_leak -q`: 1 test passed.
- `python3 -m pytest tests/test_generation_validators.py -q`: 53 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 581 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2461 total tests passed at 93.64% coverage.
