# Sprint 245 Change Log - Audit Root Path Hygiene

## Summary

- Audit root path hygiene keeps legacy local audit artifacts anchored to an explicit production path.
- `JEDI_AUDIT_ROOT` must be an absolute path in production.
- Added a production startup regression test for relative `JEDI_AUDIT_ROOT` values.
- Updated runtime validation so production deployments reject non-absolute, whitespace, or control-character audit roots before the API or worker starts.
- Documented that hosted deployments must not depend on a relative working directory for audit evidence.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_validate_runtime_settings_rejects_relative_audit_root_in_production -q`
  - `1 passed`
- `python3 -m pytest tests/test_project_docs.py -q`
  - `319 passed`
- `python3 -m ruff check src tests`
  - `All checks passed!`
- `python3 -m mypy src tests`
  - `Success: no issues found in 174 source files`
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`
  - `1598 passed, 93.93% coverage`
