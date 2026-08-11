# Sprint 735 Change Log - Stable artifact hash cause boundary

## Scope

Hardened shared artifact provenance hash diagnostics so payload validation and JSON encoder failures
do not retain unsafe low-level exception instances as public `ValueError` causes.

## Tests First

- Added 3 failing-first stable artifact hash cause assertions:
  - `tests/test_models.py::test_stable_artifact_hash_rejects_non_finite_values_without_payload_leak`
  - `tests/test_models.py::test_stable_artifact_hash_rejects_non_json_values_without_payload_leak`
  - `tests/test_models.py::test_stable_artifact_hash_rejects_string_subclass_values_without_payload_leak`
- Initial failures proved the public `ValueError` retained unsafe causes for:
  - `bad_score` non-finite numeric payload rejection.
  - `StringifiesSecret` unsupported object payload rejection.
  - `HostileHashText` string subclass payload rejection.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_735_documents_stable_artifact_hash_cause_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Suppressed original non-finite numeric validation causes in `stable_artifact_hash()`.
- Suppressed original non-JSON structure validation causes in `stable_artifact_hash()`.
- Suppressed fallback JSON encoder causes in `stable_artifact_hash()`.
- Preserved the existing fixed diagnostics:
  - `artifact hash payload contains non-finite numeric values`
  - `artifact hash payload contains non-JSON values`
- Documented the stable artifact hash cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_models.py -q -k "stable_artifact_hash_rejects"` failed first with
  3 failures.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_735` failed first with 1 failure.
- `python3 -m pytest tests/test_models.py -q -k "stable_artifact_hash_rejects"` passed with 3 tests
  and 15 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_735` passed with 1 test and 808
  deselected.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_models.py -q` passed with 18 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3062 tests and 93.33% total coverage.
