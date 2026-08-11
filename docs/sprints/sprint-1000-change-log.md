# Sprint 1000 Change Log - Catalog metadata record collection guard

## Summary

Hardened Catalog Item generation so ServiceNow metadata discovery results are validated before catalog resolution iterates records or reads record fields.

## Security

`_resolve_catalog_context()` and `_resolve_variable_sets()` now route catalog, category, taxonomy, Employee Center topic, content-type, and variable-set `fetch_table_records()` responses through `_catalog_metadata_records()`.

The helper accepts only exact Python lists containing exact Python dictionaries and fails closed with `catalog item generation field contains non-JSON value`.

Malformed metadata result containers fail before list iteration, record `.get()` hooks, active record filtering, display matching, `sys_id` extraction, relationship XML generation, ServiceNow import, or story writeback can consume caller-controlled container behavior.

## Tests

- Added 1 failing-first catalog metadata record collection subclass assertion: `test_catalog_item_customer_updates_rejects_metadata_record_collection_subclass`.
- Added 1 failing-first catalog metadata record subclass assertion: `test_catalog_item_customer_updates_rejects_metadata_record_subclass`.
- Added 1 documentation assertion: `test_sprint_1000_documents_catalog_metadata_record_collection_guard`.

## Verification

- `pytest tests/test_catalog_item_generation.py::test_catalog_item_customer_updates_rejects_metadata_record_collection_subclass tests/test_catalog_item_generation.py::test_catalog_item_customer_updates_rejects_metadata_record_subclass -q` failed before implementation because unsafe list iteration and record `.get()` hooks executed.
- `pytest tests/test_catalog_item_generation.py::test_catalog_item_customer_updates_rejects_metadata_record_collection_subclass tests/test_catalog_item_generation.py::test_catalog_item_customer_updates_rejects_metadata_record_subclass tests/test_catalog_item_generation.py::test_catalog_item_customer_updates_rejects_dict_subclass_metadata_without_leak tests/test_catalog_item_generation.py::test_catalog_item_customer_updates_rejects_matched_topic_missing_sys_id tests/test_catalog_item_generation.py::test_catalog_item_customer_updates_builds_item_variables_category_and_topic_payloads -q` - 5 passed.
