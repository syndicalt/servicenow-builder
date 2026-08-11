# Sprint 761 Change Log - Runtime worker float cause boundary

## Scope

Hardened runtime worker float setting diagnostics so parser failures do not retain unsafe lower-level parser exceptions as public worker configuration causes.

## Tests First

- Added 1 failing-first runtime worker float cause assertion:
  - `tests/test_runtime_worker_retention.py::test_worker_optional_float_wraps_unstringifiable_parser_errors`
- Initial failure proved a hostile parser exception for `JEDI_WORKER_IDLE_SLEEP_SECONDS` still appeared on the public `ValueError.__cause__` even though the visible diagnostic was already redacted.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_761_documents_runtime_worker_float_cause_boundary`
- The documentation assertion was added before the sprint log and operator guide update, so the docs gate covers the new operator-facing contract.

## Changes

- Suppressed original runtime worker float parser causes in `_optional_float()`.
- Preserved fixed diagnostics such as `runtime worker raised unstringifiable UnstringifiableWorkerFloatError`.
- Documented the runtime worker float cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime_worker_retention.py -q -k optional_float_wraps_unstringifiable_parser_errors` - 1 passed, 34 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_761` - 1 passed, 834 deselected.
- `python3 -m pytest tests/test_runtime_worker_retention.py -q` - 35 passed.
- `ruff check src tests` - passed.
- `mypy src tests` - passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 3104 passed, 93.39% coverage.
