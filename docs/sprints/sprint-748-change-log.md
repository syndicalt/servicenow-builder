# Sprint 748 Change Log - Flow XML shape evidence cause boundary

## Scope

Hardened Flow XML shape evidence validation diagnostics so malformed XML parse failures do not retain unsafe low-level XML parser exceptions as public `ValueError` causes.

## Tests First

- Added 1 failing-first Flow XML shape evidence cause assertion:
  `tests/test_generation_validators.py::test_flow_xml_shape_evidence_validator_rejects_malformed_xml_without_cause`
- Initial failure proved the public `ValueError` retained the XML parser cause for malformed Flow XML shape evidence.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_748_documents_flow_xml_shape_evidence_cause_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Suppressed original XML parser causes in `validate_flow_xml_shape_evidence()` for malformed XML evidence.
- Preserved the existing fixed diagnostic:
  - `Flow XML shape evidence is not valid XML`
- Documented the Flow XML shape evidence cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_generation_validators.py -q -k "flow_xml_shape_evidence_validator_rejects_malformed_xml_without_cause"` failed first, then passed.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_748` failed first, then passed.
- `ruff check src tests` passed.
- `mypy src tests` passed.
- `python3 -m pytest tests/test_generation_validators.py -q` passed: 58 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed: 3079 passed, 93.33% coverage.
