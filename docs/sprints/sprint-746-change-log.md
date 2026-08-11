# Sprint 746 Change Log - Admin artifact payload cause boundary

## Scope

Hardened admin artifact payload diagnostic JSON rendering so non-finite diagnostic payload failures
do not retain unsafe low-level JSON encoder exceptions as public `ValueError` causes.

## Tests First

- Added 1 failing-first admin artifact payload cause assertion:
  - `tests/test_runtime.py::test_admin_artifact_payload_json_rejects_non_finite_payload_without_leak`
- Initial failure proved the public `ValueError` retained the JSON encoder cause for:
  - Admin diagnostic payload `risk_score` non-finite numeric rejection with `do-not-echo-this` in the
    same payload.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_746_documents_admin_artifact_payload_cause_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Suppressed original JSON encoder causes in `_admin_artifact_payload_json()` for non-finite
  diagnostic payload failures.
- Preserved the existing fixed diagnostic:
  - `admin artifact payload diagnostic contains non-finite numeric values`
- Documented the admin artifact payload cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "admin_artifact_payload_json_rejects_non_finite"`
  failed first with 1 failure.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_746` failed first with 1 failure.
- `python3 -m pytest tests/test_runtime.py -q -k "admin_artifact_payload_json_rejects_non_finite"`
  passed with 1 test and 336 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_746` passed with 1 test and 819
  deselected.
- `ruff check src tests` passed after formatting the Sprint 746 docs assertion.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_runtime.py -q` passed with 337 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3076 tests and 93.33% total coverage.
