# Sprint 491 Change Log

## Operational lifecycle event non-JSON payload rejection

Hardened `PostgresOperationalStore.record_lifecycle_event()` so lifecycle event JSONB evidence cannot be written from unsupported Python payload values coerced through `str()`.

Sprint 468 rejected non-finite numeric lifecycle payload values. This sprint closes the adjacent structural JSON gap: corrupted in-process lifecycle events containing unsupported objects, bytes, or other non-JSON values now fail before transaction start, event insert, or idempotency lookup. The fixed diagnostic is `operational lifecycle event payload contains non-JSON values`, and it does not echo malformed field names, ServiceNow sys_ids, correlation ids, object type names, object string output, credential-like keys, or values.

The implementation keeps valid Pydantic-native lifecycle values such as datetimes and enums supported by preflighting the Python-mode payload and then serializing through Pydantic JSON-mode output before strict JSONB persistence.

## Verification

- Added 1 failing-first operational-store test proving an object with secret-bearing `__str__` output was previously accepted into the database path.
- `python3 -m pytest tests/test_operational_store.py::test_record_lifecycle_event_rejects_non_json_payload_before_transaction -q`: failed before implementation because the store entered the database path instead of rejecting the payload.
- `python3 -m pytest tests/test_operational_store.py::test_record_lifecycle_event_rejects_non_json_payload_before_transaction tests/test_operational_store.py::test_record_lifecycle_event_rejects_non_finite_payload_before_transaction tests/test_operational_store.py::test_record_lifecycle_event_uses_postgres_idempotency -q`: 3 tests passed.
- `python3 -m pytest tests/test_operational_store.py -q`: 47 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 565 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2425 total tests passed at 93.77% coverage.
