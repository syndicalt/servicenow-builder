# Sprint 941 Change Log - Operational-store container-subclass JSONB boundaries

## Scope

- Hardened `_ensure_lifecycle_event_payload_json_safe()` so lifecycle event JSONB payloads traverse only exact dictionaries, lists, and tuples.
- Hardened `_ensure_operational_artifact_payload_json_safe()` so DB-backed artifact JSONB payloads traverse only exact dictionaries, lists, and tuples.
- Documented operational-store lifecycle and artifact container-subclass boundaries in the operator guide.

## Production Hardening

- Lifecycle event payload dictionary, list, and tuple subclasses now fail before `items()`, iteration, transaction start, event insert, or idempotency lookup.
- Operational artifact payload dictionary, list, and tuple subclasses now fail before `items()`, iteration, hash computation, transaction start, `artifact_blobs` insert, or `artifact_refs` insert.
- Exact dictionaries, lists, and tuples remain supported for operational-store JSONB preflight.

## Tests

- Added `test_lifecycle_event_payload_rejects_container_subclasses_without_payload_leak`.
- Added `test_operational_artifact_payload_rejects_container_subclasses_without_payload_leak`.
- Added `test_sprint_941_documents_operational_store_container_subclass_boundaries`.
- Captured 2 failing-first operational-store container-subclass assertions.
- Focused verification: `3 passed`.
- Scoped verification: `54 passed`; `1014 passed`.
- Static verification: `ruff check src tests`; `mypy src tests`.
- Full coverage verification: `3600 passed`; total coverage `93.42%`.
