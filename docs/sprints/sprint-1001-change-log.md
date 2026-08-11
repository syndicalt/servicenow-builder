# Sprint 1001 Change Log - Record Producer metadata record collection guard

## Summary

Hardened Record Producer generation so ServiceNow metadata discovery results are validated before target-table checks, mapped-field iteration, catalog resolution, or category matching.

## Security

`_require_target_table()`, `_require_mapped_fields()`, and `_resolve_record_producer_context()` now route target-table, dictionary-field, catalog, and category `fetch_table_records()` responses through `_record_producer_metadata_records()`.

The helper accepts only exact Python lists containing exact Python dictionaries and fails closed with `record producer generation field contains non-JSON value`.

Malformed metadata result containers fail before list iteration, record `.get()` hooks, target-table existence checks, mapped-field validation, catalog/category matching, XML generation, ServiceNow import, or story writeback can consume caller-controlled container behavior.

## Tests

- Added 1 failing-first Record Producer metadata record collection subclass assertion: `test_record_producer_customer_updates_rejects_metadata_record_collection_subclass`.
- Added 1 failing-first Record Producer metadata record subclass assertion: `test_record_producer_customer_updates_rejects_metadata_record_subclass`.
- Added 1 documentation assertion: `test_sprint_1001_documents_record_producer_metadata_record_collection_guard`.

## Verification

- `pytest tests/test_record_producer_generation.py::test_record_producer_customer_updates_rejects_metadata_record_collection_subclass tests/test_record_producer_generation.py::test_record_producer_customer_updates_rejects_metadata_record_subclass -q` failed before implementation because unsafe list iteration and record `.get()` hooks executed.
- `pytest tests/test_record_producer_generation.py::test_record_producer_customer_updates_rejects_metadata_record_collection_subclass tests/test_record_producer_generation.py::test_record_producer_customer_updates_rejects_metadata_record_subclass tests/test_record_producer_generation.py::test_record_producer_customer_updates_builds_producer_variables_and_category tests/test_record_producer_generation.py::test_record_producer_customer_updates_fails_closed_for_missing_target_table tests/test_record_producer_generation.py::test_record_producer_customer_updates_fails_closed_for_unknown_mapped_field -q` - 5 passed.
