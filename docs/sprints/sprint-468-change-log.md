# Sprint 468 Change Log

## Operational lifecycle event JSONB non-finite number rejection

Hardened lifecycle event persistence so the operational store cannot write or look up audit events
from non-strict JSON containing `NaN`, `Infinity`, or `-Infinity`. Lifecycle webhook ingress already
rejects non-finite JSON, but `PostgresOperationalStore.record_lifecycle_event()` is also an internal
audit boundary and must fail closed if a corrupted in-process event object reaches it.

Lifecycle event persistence now serializes the Python-mode event payload with strict JSON numeric
handling before transaction start, event insert, or idempotency lookup. Non-finite lifecycle event
payloads fail with `operational lifecycle event payload contains non-finite numeric values`. The
diagnostic is stable, does not echo field names, ServiceNow sys_ids, correlation ids, or values, and
suppresses Pydantic serializer warnings for malformed in-process event objects.

## Verification

- Added 1 failing-first operational-store lifecycle event test covering non-finite event payload
  rejection before transaction start or SQL execution.
- `python3 -m pytest tests/test_operational_store.py::test_record_lifecycle_event_rejects_non_finite_payload_before_transaction -q`:
  failed before implementation because the store reached SQL and attempted idempotency lookup with
  `nan`.
- `python3 -m pytest tests/test_operational_store.py::test_record_lifecycle_event_uses_postgres_idempotency tests/test_operational_store.py::test_record_lifecycle_event_rejects_non_finite_payload_before_transaction -q`:
  2 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 542 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`:
  2378 total tests passed at 93.84% coverage.
