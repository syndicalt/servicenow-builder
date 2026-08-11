# Sprint 740 Change Log - Operational store JSONB cause boundary

## Scope

Hardened operational-store JSONB diagnostics so lifecycle event payload and artifact payload
validation failures do not retain unsafe low-level exception instances as public `ValueError` causes.

## Tests First

- Added 6 failing-first operational store cause assertions:
  - `tests/test_operational_store.py::test_record_lifecycle_event_rejects_non_finite_payload_before_transaction`
  - `tests/test_operational_store.py::test_record_lifecycle_event_rejects_non_json_payload_before_transaction`
  - `tests/test_operational_store.py::test_record_lifecycle_event_rejects_string_subclass_payload_before_transaction`
  - `tests/test_operational_store.py::test_record_json_artifact_rejects_non_finite_payload_before_transaction`
  - `tests/test_operational_store.py::test_record_json_artifact_rejects_non_json_payload_before_transaction`
  - `tests/test_operational_store.py::test_record_json_artifact_rejects_string_subclass_payload_before_transaction`
- Initial failures proved the public `ValueError` retained unsafe causes for:
  - Lifecycle event non-finite payload rejection.
  - Lifecycle event `StringifiesSecret` unsupported object rejection.
  - Lifecycle event `HostileLifecycleText` string subclass rejection.
  - Artifact payload `bad_score` non-finite payload rejection.
  - Artifact payload `StringifiesSecret` unsupported object rejection.
  - Artifact payload `HostileArtifactText` string subclass rejection.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_740_documents_operational_store_jsonb_cause_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Suppressed original Pydantic serializer causes in `record_lifecycle_event()`.
- Suppressed original non-finite numeric validation causes in `record_lifecycle_event()`.
- Suppressed original non-JSON structure validation causes in `record_lifecycle_event()`.
- Suppressed original non-finite numeric validation causes in `record_json_artifact()`.
- Suppressed original non-JSON structure validation causes in `record_json_artifact()`.
- Preserved the existing fixed diagnostics:
  - `operational lifecycle event payload contains non-finite numeric values`
  - `operational lifecycle event payload contains non-JSON values`
  - `operational artifact JSON payload contains non-finite numeric values`
  - `operational artifact JSON payload contains non-JSON values`
- Documented the operational store JSONB cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_operational_store.py -q -k "record_json_artifact_rejects or record_lifecycle_event_rejects"`
  failed first with 6 failures.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_740` failed first with 1 failure.
- `python3 -m pytest tests/test_operational_store.py -q -k "record_json_artifact_rejects or record_lifecycle_event_rejects"`
  passed with 6 tests and 44 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_740` passed with 1 test and 813
  deselected.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_operational_store.py -q` passed with 50 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3070 tests and 93.33% total coverage.
