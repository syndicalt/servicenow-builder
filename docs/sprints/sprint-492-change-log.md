# Sprint 492 Change Log

## Operational artifact JSONB non-JSON payload rejection

Hardened `PostgresOperationalStore.record_json_artifact()` so DB-backed artifact JSONB evidence cannot fail through raw `TypeError` diagnostics when a corrupted in-process artifact payload contains unsupported Python values.

Sprint 464 rejected non-finite numeric artifact payloads before hash computation or transaction start. This sprint closes the adjacent structural JSON gap: unsupported objects, bytes, and other non-JSON payload values now fail before SHA-256 computation, transaction start, `artifact_blobs` insert, or `artifact_refs` insert. The fixed diagnostic is `operational artifact JSON payload contains non-JSON values`, and it does not echo malformed field names, object type names, object string output, credential-like keys, or values.

## Verification

- Added 1 failing-first operational-store artifact test proving an object with secret-bearing `__str__` output previously escaped as a raw JSON `TypeError`.
- `python3 -m pytest tests/test_operational_store.py::test_record_json_artifact_rejects_non_json_payload_before_transaction -q`: failed before implementation because the raw `TypeError` reflected the object type name.
- `python3 -m pytest tests/test_operational_store.py::test_record_json_artifact_rejects_non_json_payload_before_transaction tests/test_operational_store.py::test_record_json_artifact_rejects_non_finite_payload_before_transaction tests/test_operational_store.py::test_record_json_artifact_persists_payload_and_db_backed_ref -q`: 3 tests passed.
- `python3 -m pytest tests/test_operational_store.py -q`: 48 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 566 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2427 total tests passed at 93.77% coverage.
