# Sprint 510 Change Log

## UI Policy generation field non-JSON value rejection

Hardened UI Policy customer-update generation so raw declarative form-behavior candidate fields are not implicitly stringified before policy/action matching, tristate validation, forbidden-token scanning, or XML generation.

`ui_policy_customer_updates()` now rejects unsupported objects, bytes, containers in scalar positions, floats, and non-scalar values in policy names, target tables, conditions, descriptions, views, flags, order values, action policy names, action tables, action fields, tristate action values, and clear-value flags with the fixed `UI Policy generation field contains non-JSON value` diagnostic. The diagnostic does not echo field names, object type names, object string output, credential-like keys, conditions, descriptions, view names, or action field values.

This preserves valid UI Policy behavior, including action table defaults, read-only aliases, ignored tristate values, and non-numeric order defaults, while closing the boundary before policy/action matching, tristate validation, forbidden-token scanning, XML generation, ServiceNow import, or story writeback.

## Verification

- Added 1 failing-first UI Policy generation test proving a secret-bearing UI Policy field object was previously stringified before validation.
- `python3 -m pytest tests/test_generation_validators.py::test_ui_policy_customer_updates_rejects_non_json_field_without_leak -q`: failed before implementation because the strict diagnostic did not exist.
- `python3 -m pytest tests/test_generation_validators.py::test_ui_policy_customer_updates_rejects_non_json_field_without_leak -q`: 1 test passed.
- `python3 -m pytest tests/test_generation_validators.py -q`: 56 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 584 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2467 total tests passed at 93.55% coverage.
