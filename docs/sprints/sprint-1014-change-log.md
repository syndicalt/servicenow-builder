# Sprint 1014 Change Log - Operational store scalar read guard

## Summary
Hardened operational-store scalar reads so database-returned identifiers and counters are exact integers before they drive follow-on writes, audit totals, or loop decisions.

## Security
Artifact blob id extraction and retention prune count handling now route database-returned scalar values through `_operational_read_int()`.

The helper accepts only exact Python integers at or above the call-site minimum and fails closed with `operational store read scalar is unsafe`.

Malformed operational-store scalar results fail before `int()` coercion, artifact reference insertion, retention audit writes, retention batch-loop termination checks, admin reporting, or API JSON serialization can consume caller-controlled scalar behavior.

## Tests
- Added 1 failing-first artifact blob id object assertion: `test_record_json_artifact_rejects_blob_id_object_before_int_conversion`.
- Added 1 invalid artifact blob id scalar matrix: `test_record_json_artifact_rejects_invalid_blob_id_scalars`.
- Added 1 failing-first retention deleted-count object assertion: `test_prune_expired_records_rejects_count_object_without_leak`.
- Added 1 invalid retention deleted-count scalar matrix: `test_prune_expired_records_rejects_invalid_deleted_count_scalars`.
- Added 1 documentation assertion: `test_sprint_1014_documents_operational_store_scalar_read_guard`.

## Verification
- `pytest tests/test_operational_store.py::test_record_json_artifact_rejects_blob_id_object_before_int_conversion tests/test_operational_store.py::test_prune_expired_records_rejects_count_object_without_leak -q` failed before implementation because hostile scalar `__int__` hooks executed.
- `pytest tests/test_operational_store.py::test_record_json_artifact_rejects_blob_id_object_before_int_conversion tests/test_operational_store.py::test_record_json_artifact_rejects_invalid_blob_id_scalars tests/test_operational_store.py::test_prune_expired_records_rejects_count_object_without_leak tests/test_operational_store.py::test_prune_expired_records_rejects_invalid_deleted_count_scalars tests/test_operational_store.py::test_record_json_artifact_persists_payload_and_db_backed_ref tests/test_operational_store.py::test_prune_expired_records_deletes_only_terminal_expired_records -q` - 9 passed.
