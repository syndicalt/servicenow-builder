# Sprint 947 Change Log - Catalog item container-subclass guard

## Scope

- Hardened `_variable_set_names()` so Catalog Item customer-update generation accepts only exact lists before variable-set iteration.
- Hardened `_variable_group_intents()` so variable group arrays must be exact lists and group mapping entries must be exact dictionaries before validation.
- Hardened `_reference_value()` so discovered ServiceNow reference metadata must be an exact dictionary before `value` or `display_value` lookup.
- Documented the Catalog Item container-subclass boundary in the operator guide.

## Production Hardening

- List and dictionary subclasses now fail with `catalog item generation field contains non-JSON value` before catalog item XML generation.
- Catalog Item generation no longer allows caller-controlled list iterators or dictionary accessors to run while parsing variable sets or resolving ServiceNow reference metadata.
- Exact JSON list and dictionary inputs remain supported for variable sets, variable groups, and ServiceNow reference metadata.

## Tests

- Added `test_catalog_item_customer_updates_rejects_list_subclass_item_field_without_leak`.
- Added `test_catalog_item_customer_updates_rejects_dict_subclass_metadata_without_leak`.
- Captured 2 failing-first catalog item container-subclass execution assertions.
- Focused verification passed: 4 tests, including the Sprint 917 diagnostic-doc correction.
- Scoped verification passed: `tests/test_catalog_item_generation.py` 52 tests and `tests/test_project_docs.py` 1020 tests.
- Static verification passed: `python3 -m ruff check src tests` and `python3 -m mypy src tests`.
- Full coverage verification passed: 3618 tests at 93.25% coverage.
