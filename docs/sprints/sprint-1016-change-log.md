# Sprint 1016 Change Log - Operational store payload traversal guard

## Summary
Hardened operational-store record payload validation so exact JSON containers are cycle-safe and depth-bounded before model hydration.

## Security
`_ensure_operational_record_payload_json_safe()` now tracks active exact dictionaries and lists and caps traversal with `MAX_OPERATIONAL_RECORD_PAYLOAD_DEPTH`.

Cyclic payloads, repeated active containers, and excessively nested payloads fail closed with `operational store record payload is unsafe`.

Malformed operational-store record payloads fail before recursive validation, Pydantic model hydration, admin rendering, API JSON serialization, work-note routing, worker status reporting, or artifact reference reporting can recurse indefinitely or expose payload fragments through traversal failures.

## Tests
- Added 1 failing-first cyclic operational-store payload assertion: `test_lifecycle_event_record_rejects_cyclic_payload_without_leak`.
- Added 1 failing-first over-depth operational-store payload assertion: `test_lifecycle_event_record_rejects_excessively_nested_payload_without_leak`.
- Added 1 documentation assertion: `test_sprint_1016_documents_operational_store_payload_traversal_guard`.

## Verification
- `pytest tests/test_operational_store.py::test_lifecycle_event_record_rejects_cyclic_payload_without_leak tests/test_operational_store.py::test_lifecycle_event_record_rejects_excessively_nested_payload_without_leak -q` failed before implementation because cyclic payloads raised `RecursionError` and over-depth payloads were accepted.
- `pytest tests/test_operational_store.py::test_lifecycle_event_record_rejects_cyclic_payload_without_leak tests/test_operational_store.py::test_lifecycle_event_record_rejects_excessively_nested_payload_without_leak tests/test_operational_store.py::test_record_json_artifact_persists_payload_and_db_backed_ref tests/test_operational_store.py::test_lifecycle_event_record_rejects_payload_subclass_without_leak -q` - 4 passed.
