# Sprint 506 Change Log

## Catalog item generation field non-JSON value rejection

Hardened catalog item customer-update generation so raw item fields, variable fields, variable set names, compact group declarations, fulfillment flow names, active flags, display fields, sys_ids, and related reference values are not implicitly stringified before catalog metadata resolution or XML generation.

`catalog_item_customer_updates()` now rejects unsupported objects, bytes, containers in scalar positions, floats, and non-scalar values with the fixed `catalog item generation field contains non-JSON value` diagnostic. The diagnostic does not echo field names, object type names, object string output, credential-like keys, item values, variable metadata, discovered ServiceNow metadata, or reference values.

This preserves valid catalog item behavior, including explicit list and object shapes for variable sets and typed variable groups, while closing scalar boundaries before catalog/category/topic/flow resolution, metadata lookup, XML generation, ServiceNow import, or story writeback.

## Verification

- Added 1 failing-first catalog item generation test proving a secret-bearing catalog item object was previously stringified before metadata lookup.
- `python3 -m pytest tests/test_catalog_item_generation.py::test_catalog_item_customer_updates_rejects_non_json_item_field_without_leak -q`: failed before implementation because the strict diagnostic did not exist.
- `python3 -m pytest tests/test_catalog_item_generation.py::test_catalog_item_customer_updates_rejects_non_json_item_field_without_leak -q`: 1 test passed.
- `python3 -m pytest tests/test_catalog_item_generation.py -q`: 46 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 580 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2459 total tests passed at 93.67% coverage.
