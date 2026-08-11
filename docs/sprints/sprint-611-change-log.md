# Sprint 611 Change Log

## Operational artifact exact-string JSONB boundary

Sprint 611 continued production hardening by requiring exact string values before DB-backed JSON artifacts are accepted for operational-store persistence. `record_json_artifact()` already rejected non-finite numeric values and unsupported non-JSON values before hash computation or transaction start, but direct `json.dumps()` accepted string subclasses and allowed subclassed text to enter the canonical payload and SHA-256 provenance hash.

`_ensure_operational_artifact_payload_json_safe()` now preflights DB-backed artifact payloads before canonical serialization. It accepts exact `str` values and exact `str` mapping keys only. String subclasses fail through the same `operational artifact JSON payload contains non-JSON values` diagnostic as other unsupported values, without echoing payload field names, credential-like keys, object output, or values.

Verification:

- Added 1 failing-first operational-store artifact test proving a string subclass payload value reached the INSERT path and canonical payload before implementation.
- `python3 -m pytest tests/test_operational_store.py::test_record_json_artifact_rejects_string_subclass_payload_before_transaction -q`: failed before implementation because the subclassed value reached `INSERT INTO artifact_blobs` instead of raising `ValueError` before hash computation or transaction start.
- `python3 -m pytest tests/test_operational_store.py::test_record_json_artifact_rejects_string_subclass_payload_before_transaction tests/test_operational_store.py::test_record_json_artifact_rejects_non_finite_payload_before_transaction tests/test_operational_store.py::test_record_json_artifact_rejects_non_json_payload_before_transaction tests/test_operational_store.py::test_record_json_artifact_persists_payload_and_db_backed_ref -q`: 4 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_611_documents_operational_artifact_exact_string_boundary tests/test_project_docs.py::test_sprint_492_documents_operational_artifact_jsonb_non_json_rejection -q`: 2 passed.
- `python3 -m pytest tests/test_operational_store.py -q`: 50 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 685 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2702 passed, total coverage 93.13%, required 90% coverage reached.
