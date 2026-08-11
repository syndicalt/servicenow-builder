# Sprint 737 Change Log - Model fulfillment artifact payload cause boundary

## Scope

Hardened model fulfillment artifact payload diagnostics so payload validation, Pydantic serializer,
and JSON encoder failures do not retain unsafe low-level exception instances as public `ValueError`
causes.

## Tests First

- Added 3 failing-first model fulfillment artifact payload cause assertions:
  - `tests/test_model_fulfillment.py::test_model_artifact_payload_rejects_non_finite_candidate_fields_without_leak`
  - `tests/test_model_fulfillment.py::test_model_artifact_payload_rejects_non_json_candidate_fields_without_leak`
  - `tests/test_model_fulfillment.py::test_model_artifact_payload_rejects_string_subclass_candidate_fields_without_leak`
- Initial failures proved the public `ValueError` retained unsafe causes for:
  - `weight` non-finite candidate artifact payload rejection.
  - `SecretBearingObject` unsupported candidate artifact payload rejection.
  - `HostileModelArtifactText` string subclass candidate artifact payload rejection.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_737_documents_model_fulfillment_artifact_payload_cause_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Suppressed original Pydantic serializer causes in `_model_artifact_payload()`.
- Suppressed original non-finite numeric validation causes in `_model_artifact_payload()`.
- Suppressed original non-JSON structure validation causes in `_model_artifact_payload()`.
- Preserved the existing fixed diagnostics:
  - `model fulfillment artifact payload contains non-finite numeric values`
  - `model fulfillment artifact payload contains non-JSON values`
- Documented the model fulfillment artifact payload cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_model_fulfillment.py -q -k model_artifact_payload_rejects` failed
  first with 3 failures.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_737` failed first with 1 failure.
- `python3 -m pytest tests/test_model_fulfillment.py -q -k model_artifact_payload_rejects` passed
  with 3 tests and 33 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_737` passed with 1 test and 810
  deselected.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_model_fulfillment.py -q` passed with 36 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3064 tests and 93.33% total coverage.
