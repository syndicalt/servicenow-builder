# Sprint 464 Change Log

## Operational artifact JSONB non-finite number rejection

Hardened the PostgreSQL operational-store artifact boundary so DB-backed artifact payloads cannot
be serialized into `artifact_blobs.payload_json` with non-standard JSON numeric constants such as
`NaN`, `Infinity`, or `-Infinity`. The canonical payload string is used both for JSONB persistence
and SHA-256 provenance, so accepting Python's default `json.dumps()` behavior would allow invalid
JSON evidence and a hash over that invalid representation.

`record_json_artifact()` now serializes canonical payloads with strict JSON numeric handling and
raises the fixed `operational artifact JSON payload contains non-finite numeric values` diagnostic
before hash computation, transaction start, `artifact_blobs` insert, or `artifact_refs` insert. The
diagnostic does not echo payload field names, credential-like keys, or values.

## Verification

- Added 1 failing-first operational-store artifact test covering non-finite payload rejection before
  transaction start or SQL execution.
- `python3 -m pytest tests/test_operational_store.py::test_record_json_artifact_rejects_non_finite_payload_before_transaction -q`:
  failed before implementation because `NaN` was serialized into the SQL JSONB parameter.
- `python3 -m pytest tests/test_operational_store.py::test_record_json_artifact_persists_payload_and_db_backed_ref tests/test_operational_store.py::test_record_json_artifact_rejects_non_finite_payload_before_transaction tests/test_operational_store.py::test_artifact_refs_include_artifact_id_when_present tests/test_operational_store.py::test_get_artifact_blob_returns_typed_payload -q`:
  4 tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 538 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`:
  2369 total tests passed at 93.83% coverage.
