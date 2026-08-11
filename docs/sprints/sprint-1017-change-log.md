# Sprint 1017 Change Log - Retention prune report hydration guard

## Summary
Hardened retention prune report hydration so operational maintenance evidence is exact-shape validated before audit output.

## Security
`RetentionClassPruneResult` now requires exact string record classes, exact datetimes, exact non-negative deleted counts, and exact positive batch counts.

`RetentionPruneReport` now requires exact booleans, exact datetimes, exact positive prune batch sizes, and exact lists of already-validated `RetentionClassPruneResult` objects.

Malformed retention report values fail closed with `operational store retention report scalar is unsafe` or `operational store retention report results are unsafe` before Pydantic coercion, audit JSON rendering, worker log output, admin reporting, or API serialization can convert malformed maintenance evidence into an official report.

## Tests
- Added 1 failing-first retention report text subclass assertion: `test_retention_prune_result_rejects_record_class_string_subclass_without_leak`.
- Added 1 invalid retention report count scalar matrix: `test_retention_prune_result_rejects_invalid_count_scalars`.
- Added 1 failing-first retention report results collection assertion: `test_retention_prune_report_rejects_results_collection_subclass_without_leak`.
- Added 1 documentation assertion: `test_sprint_1017_documents_retention_prune_report_hydration_guard`.

## Verification
- `pytest tests/test_operational_store.py::test_retention_prune_result_rejects_record_class_string_subclass_without_leak tests/test_operational_store.py::test_retention_prune_result_rejects_invalid_count_scalars tests/test_operational_store.py::test_retention_prune_report_rejects_results_collection_subclass_without_leak -q` failed before implementation because Pydantic accepted unsafe report inputs.
- `pytest tests/test_operational_store.py::test_retention_prune_result_rejects_record_class_string_subclass_without_leak tests/test_operational_store.py::test_retention_prune_result_rejects_invalid_count_scalars tests/test_operational_store.py::test_retention_prune_report_rejects_results_collection_subclass_without_leak tests/test_operational_store.py::test_prune_expired_records_is_noop_when_retention_disabled tests/test_operational_store.py::test_prune_expired_records_deletes_only_terminal_expired_records tests/test_operational_store.py::test_prune_expired_records_batches_deletes_until_drained -q` - 7 passed.
