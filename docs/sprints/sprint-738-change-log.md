# Sprint 738 Change Log - Provider contract cause boundary

## Scope

Hardened shared provider contract diagnostics so prompt payload serialization and strict response
JSON parsing failures do not retain unsafe low-level exception instances as public provider errors.

## Tests First

- Added 7 failing-first provider contract cause assertions:
  - `tests/test_provider_contract.py::test_implementation_payload_rejects_mapping_subclass_without_leak`
  - `tests/test_provider_contract.py::test_implementation_payload_rejects_key_subclass_without_normalization`
  - `tests/test_provider_contract.py::test_implementation_payload_rejects_list_subclass_without_leak`
  - `tests/test_provider_contract.py::test_implementation_payload_rejects_string_subclass_without_normalization`
  - `tests/test_provider_contract.py::test_implementation_payload_rejects_non_finite_number_without_cause`
  - `tests/test_provider_contract.py::test_loads_strict_json_object_invalid_json_does_not_retain_parser_cause`
  - `tests/test_provider_contract.py::test_loads_strict_json_object_non_finite_json_does_not_retain_parser_cause`
- Initial failures proved the public provider errors retained unsafe causes for:
  - `HostilePayload` mapping subclass prompt payload rejection.
  - `SneakyKey` key subclass prompt payload rejection.
  - `HostileList` list subclass prompt payload rejection.
  - `SneakyString` string subclass prompt payload rejection.
  - Non-finite prompt payload numeric rejection.
  - Malformed provider response JSON containing `provider-response-secret`.
  - Non-finite provider response JSON containing `provider-response-secret`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_738_documents_provider_contract_cause_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Suppressed original `TypeError` causes when unsupported provider prompt payload structures are
  rejected.
- Suppressed original `ValueError` causes when non-finite provider prompt payload numbers are
  rejected.
- Suppressed original `JSONDecodeError` and parser `ValueError` causes when strict provider response
  JSON parsing fails.
- Preserved the existing fixed diagnostics:
  - `Model provider prompt payload contains unsupported JSON value types`
  - `Model provider prompt payload contains non-finite numeric values`
  - Provider adapter invalid-JSON diagnostics passed into `loads_strict_json_object()`.
- Documented the provider contract cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_provider_contract.py -q -k "implementation_payload_rejects or loads_strict_json_object"`
  failed first with 7 failures.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_738` failed first with 1 failure.
- `python3 -m pytest tests/test_provider_contract.py -q -k "implementation_payload_rejects or loads_strict_json_object"`
  passed with 7 tests and 5 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_738` passed with 1 test and 811
  deselected.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_provider_contract.py -q` passed with 12 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3068 tests and 93.33% total coverage.
