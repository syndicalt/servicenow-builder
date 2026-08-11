# Sprint 1015 Change Log - Operational store record hydration guard

## Summary
Hardened operational-store record model hydration so persisted database records are exact primitive and JSON values before Pydantic validation can coerce them.

## Security
`LifecycleEventRecord`, `FulfillmentJobRecord`, `JobEventRecord`, `ArtifactRefRecord`, and `ArtifactBlobRecord` now validate record fields before model hydration.

Text fields require exact Python strings. Identifier and counter fields require exact Python integers with record-appropriate minimums. Timestamp fields require exact `datetime` values. Persisted JSON payload fields require exact dictionaries containing exact JSON primitives, lists, and dictionaries.

Malformed operational-store record values fail closed with `operational store record scalar is unsafe` or `operational store record payload is unsafe` before Pydantic coercion, model serialization, admin rendering, API JSON serialization, work-note routing, worker status reporting, or artifact reference reporting can consume caller-controlled scalar or container behavior.

## Tests
- Added 1 failing-first operational-store record text subclass assertion: `test_fulfillment_job_record_rejects_string_subclass_without_leak`.
- Added 1 failing-first lifecycle payload subclass assertion: `test_lifecycle_event_record_rejects_payload_subclass_without_leak`.
- Added 1 documentation assertion: `test_sprint_1015_documents_operational_store_record_hydration_guard`.

## Verification
- `pytest tests/test_operational_store.py::test_fulfillment_job_record_rejects_string_subclass_without_leak tests/test_operational_store.py::test_lifecycle_event_record_rejects_payload_subclass_without_leak -q` failed before implementation because string subclasses were accepted and payload subclass hooks leaked through Pydantic mapping errors.
- `pytest tests/test_operational_store.py::test_fulfillment_job_record_rejects_string_subclass_without_leak tests/test_operational_store.py::test_lifecycle_event_record_rejects_payload_subclass_without_leak tests/test_operational_store.py::test_enqueue_fulfillment_job_uses_postgres_idempotency_and_job_event tests/test_operational_store.py::test_record_json_artifact_persists_payload_and_db_backed_ref tests/test_operational_store.py::test_artifact_refs_include_artifact_id_when_present tests/test_operational_store.py::test_recent_lifecycle_events_returns_newest_events -q` - 6 passed.
