# Sprint 242 Change Log - Build Claim State Value Hygiene

## Summary

- Build claim state value hygiene prevents ambiguous ServiceNow state transitions during live production claim writes.
- Added a production startup regression test for padded `JEDI_BUILD_CLAIM_FROM_STATE` values when `JEDI_BUILD_CLAIM_APPLY=true`.
- Updated runtime validation so production deployments reject empty, padded, or control-character `JEDI_BUILD_CLAIM_FROM_STATE` and `JEDI_BUILD_CLAIM_STATE` values before the worker starts.
- Documented that state values are preferred and live build-claim write configuration must be unambiguous.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_validate_runtime_settings_rejects_padded_build_claim_states_in_production -q`
  - `1 passed`
- `python3 -m ruff check src tests`
  - `All checks passed!`
- `python3 -m mypy src tests`
  - `Success: no issues found in 174 source files`
- `python3 -m pytest tests/test_project_docs.py -q`
  - `316 passed`
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`
  - `1592 passed, 93.92% coverage`
