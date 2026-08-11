# Sprint 749 Change Log - Flow graph diff operation cause boundary

## Scope

Hardened Flow graph diff unsupported-operation diagnostics so the stable public error does not retain unsafe Pydantic validation exceptions as `ValueError` causes.

## Tests First

- Added 1 failing-first Flow graph diff operation cause assertion:
  `tests/test_generation_validators.py::test_flow_graph_diff_validator_detects_unsupported_operation_without_stringifying_error`
- Initial failure proved the public `ValueError` retained the original validation error cause for unsupported graph rewrite requests.
- The hostile validation error included `client-secret-value` to prove cause retention could preserve sensitive exception text even though `str(exc)` was not called.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_749_documents_flow_graph_diff_operation_cause_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Suppressed the original Pydantic `ValidationError` cause when `validate_flow_graph_diff_candidate()` raises `unsupported Flow graph diff operation`.
- Preserved structured validation-error location routing for the unsupported operation diagnostic.
- Preserved the existing fixed diagnostic:
  - `unsupported Flow graph diff operation`
- Documented the Flow graph diff operation cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_generation_validators.py -q -k "flow_graph_diff_validator_detects_unsupported_operation_without_stringifying_error"` failed first, then passed.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_749` failed first, then passed.
- `ruff check src tests` passed.
- `mypy src tests` passed.
- `python3 -m pytest tests/test_generation_validators.py -q` passed: 58 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed: 3080 passed, 93.33% coverage.
