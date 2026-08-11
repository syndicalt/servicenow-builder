# Sprint 1010 Change Log - Operational store schema readiness row guard

## Summary

Hardened operational-store schema readiness so database rows returned from the `information_schema.tables` readiness query are validated before required-table matching or readiness reporting.

## Security

`verify_schema_ready()` now routes each returned schema row through `_schema_readiness_table_name()`.

The helper accepts only exact Python dictionaries. The `table_name` value may be absent, `None`, or an exact Python string. Dictionary subclasses, mapping-like objects, string subclasses, and malformed table-name values fail closed with `operational store schema readiness row contains non-JSON value`.

Malformed schema readiness rows fail before row `.get()` hooks, table-presence matching, API readiness responses, admin health checks, startup probes, or logs can consume caller-controlled database row behavior.

## Tests

- Added 1 failing-first operational-store schema readiness row subclass assertion: `test_verify_schema_ready_rejects_schema_row_subclass_without_leak`.
- Added 1 documentation assertion: `test_sprint_1010_documents_operational_store_schema_readiness_row_guard`.

## Verification

- `pytest tests/test_operational_store.py::test_verify_schema_ready_rejects_schema_row_subclass_without_leak -q` failed before implementation because unsafe row `.get()` hooks executed.
- `pytest tests/test_operational_store.py::test_verify_schema_ready_checks_required_operational_tables tests/test_operational_store.py::test_verify_schema_ready_returns_false_when_required_table_is_missing tests/test_operational_store.py::test_verify_schema_ready_rejects_schema_row_subclass_without_leak -q` - 3 passed.
