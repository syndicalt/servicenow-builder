# Sprint 752 Change Log - Flow graph diff payload cause boundary

## Scope

Hardened Flow graph diff strict JSON validation so non-finite and non-JSON payload diagnostics do not retain unsafe JSON encoder exceptions as public `ValueError` causes.

## Tests First

- Added 2 failing-first Flow graph diff payload cause assertions:
  - `tests/test_generation_validators.py::test_flow_graph_diff_payload_json_rejects_non_finite_values_without_cause`
  - `tests/test_generation_validators.py::test_flow_graph_diff_payload_json_rejects_non_json_values_without_cause`
- Initial failures proved `_strict_validation_json()` retained JSON encoder exceptions for non-finite and non-JSON payload values.
- Added high-level regression assertions to the existing Flow graph diff validator tests to confirm public graph diff diagnostics still suppress causes after Pydantic validation.
- The hostile payload included `StringifiesSecret` and `do-not-echo-this` to prove diagnostics avoid payload key, value, and object representation leakage.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_752_documents_flow_graph_diff_payload_cause_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Suppressed original JSON encoder causes in `_strict_validation_json()` for non-finite payload values.
- Suppressed original JSON encoder causes in `_strict_validation_json()` for non-JSON payload values.
- Preserved existing fixed diagnostics:
  - `Flow graph diff contains a non-finite payload value`
  - `Flow graph diff contains a non-JSON payload value`
- Documented the Flow graph diff payload cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_generation_validators.py -q -k "flow_graph_diff_payload_json_rejects_non_finite_values_without_cause or flow_graph_diff_payload_json_rejects_non_json_values_without_cause"` failed first.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_752` failed first, then passed.
- `python3 -m pytest tests/test_generation_validators.py -q -k "flow_graph_diff_payload_json_rejects_non_finite_values_without_cause or flow_graph_diff_payload_json_rejects_non_json_values_without_cause or flow_graph_diff_validator_rejects_non_finite_graph_payload_without_leak or flow_graph_diff_validator_rejects_non_json_payload_values_without_leak"` passed: 4 passed.
- `ruff check src tests` passed.
- `mypy src tests` passed.
- `python3 -m pytest tests/test_generation_validators.py -q` passed: 60 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed: 3087 passed, 93.35% coverage.
