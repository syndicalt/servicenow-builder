# Sprint 763 Change Log - Explicit exception cause regression gate

## Scope

Added a source-wide regression gate so future hardening work cannot reintroduce explicit named exception causes after the diagnostic cause-boundary cleanup.

## Tests First

- Added 1 source-wide AST regression assertion:
  - `tests/test_exception_diagnostics.py::test_source_uses_only_suppressed_explicit_exception_causes`
- The test walks every Python file under `src/jedi_devproject` and fails on any explicit raise cause that is not `from None`.
- Added 1 documentation assertion:
  `tests/test_project_docs.py::test_sprint_763_documents_explicit_exception_cause_regression_gate`

## Changes

- Documented that public/operator diagnostics may preserve fixed messages but must not retain lower-level exception objects through named explicit causes.
- Established the current source invariant: no named exception causes remain in `src/jedi_devproject`; every explicit cause is suppressed with `from None`.

## Verification

- `python3 -m pytest tests/test_exception_diagnostics.py -q -k source_uses_only_suppressed_explicit_exception_causes` - 1 passed, 4 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_763` - 1 passed, 836 deselected.
- `python3 -m pytest tests/test_exception_diagnostics.py -q` - 5 passed.
- `ruff check src tests` - passed.
- `mypy src tests` - passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 3108 passed, 93.39% coverage.
