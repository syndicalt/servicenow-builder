# Sprint 511 Change Log

## Catalog UI Policy generation field non-JSON value rejection

Sprint 511 continued the production-hardening pass across generated customer-update surfaces by tightening Catalog UI Policy generation. Catalog UI Policy candidate fields can come from model output, retrieved instance context, or stored artifacts, so the generator must not coerce arbitrary Python objects into update-set XML or validation diagnostics.

`catalog_ui_policy_customer_updates()` now rejects unsupported objects, bytes, containers in scalar positions, floats, and non-scalar values in policy names, catalog item names, catalog conditions, flags, order values, script placeholders, action policy names, action variables, action tristate values, and clear-value flags with the fixed `Catalog UI Policy generation field contains non-JSON value` diagnostic. The diagnostic does not echo field names, object type names, object string output, credential-like keys, catalog conditions, catalog item names, script placeholders, or action variable values.

This keeps Catalog UI Policy handoff aligned with the hardened Dictionary, form layout, catalog item, record producer, Script Include, Business Rule, Client Script, and UI Policy paths: unsupported scalar input fails before policy/action matching, variable ownership checks, condition parsing, tristate validation, XML generation, ServiceNow import, or story writeback.

Verification:

- Added 1 failing-first Catalog UI Policy generation test covering a secret-bearing object with a hostile `__str__`.
- `python3 -m pytest tests/test_generation_validators.py::test_catalog_ui_policy_customer_updates_rejects_non_json_field_without_leak -q`: failed before implementation because the strict diagnostic did not exist.
- `python3 -m pytest tests/test_generation_validators.py::test_catalog_ui_policy_customer_updates_rejects_non_json_field_without_leak -q`: 1 test passed.
- `python3 -m pytest tests/test_generation_validators.py -q`: 57 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 585 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2469 total tests passed at 93.53% coverage.
