# Sprint 736 Change Log - Context dossier DTO cause boundary

## Scope

Hardened model-facing context dossier DTO diagnostics so payload validation, Pydantic serializer, and
JSON encoder failures do not retain unsafe low-level exception instances as public `ValueError`
causes.

## Tests First

- Added 3 failing-first context dossier DTO cause assertions:
  - `tests/test_packet_context.py::test_context_model_payload_rejects_non_finite_dto_without_payload_leak`
  - `tests/test_packet_context.py::test_context_model_payload_rejects_non_json_dto_without_payload_leak`
  - `tests/test_packet_context.py::test_context_model_payload_rejects_string_subclass_dto_without_payload_leak`
- Initial failures proved the public `ValueError` retained unsafe causes for:
  - `confidence` non-finite DTO payload rejection.
  - `SecretBearingObject` unsupported DTO payload rejection.
  - `HostileContextText` string subclass DTO payload rejection.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_736_documents_context_dossier_dto_cause_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Suppressed original Pydantic serializer causes in `_context_model_payload()`.
- Suppressed original non-finite numeric validation causes in `_context_model_payload()`.
- Suppressed original non-JSON structure validation causes in `_context_model_payload()`.
- Preserved the existing fixed diagnostics:
  - `context dossier DTO payload contains non-finite numeric values`
  - `context dossier DTO payload contains non-JSON values`
- Documented the context dossier DTO cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_packet_context.py -q -k context_model_payload` failed first with 3
  failures.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_736` failed first with 1 failure.
- `python3 -m pytest tests/test_packet_context.py -q -k context_model_payload` passed with 3 tests.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_736` passed with 1 test and 809
  deselected.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_packet_context.py -q` passed with 3 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3063 tests and 93.33% total coverage.
