# Sprint 509 Change Log

## Client Script generation field non-JSON value rejection

Hardened Client Script customer-update generation so raw browser-side executable candidate fields are not implicitly stringified before script type validation, script safety scanning, field-write validation, or XML generation.

`client_script_customer_updates()` now rejects unsupported objects, bytes, containers in scalar positions, floats, and non-scalar values in target table, script name, script type, watched field, script body, declared field access metadata, and user-facing message metadata with the fixed `Client Script generation field contains non-JSON value` diagnostic. The diagnostic does not echo field names, object type names, object string output, credential-like keys, generated script bodies, watched field names, or message text.

This preserves valid Client Script behavior while closing the boundary before script type validation, script safety scanning, field-write validation, XML generation, ServiceNow import, or story writeback.

## Verification

- Added 1 failing-first Client Script generation test proving a secret-bearing Client Script field object was previously stringified before validation.
- `python3 -m pytest tests/test_generation_validators.py::test_client_script_customer_updates_rejects_non_json_field_without_leak -q`: failed before implementation because the strict diagnostic did not exist.
- `python3 -m pytest tests/test_generation_validators.py::test_client_script_customer_updates_rejects_non_json_field_without_leak -q`: 1 test passed.
- `python3 -m pytest tests/test_generation_validators.py -q`: 55 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 583 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2465 total tests passed at 93.54% coverage.
