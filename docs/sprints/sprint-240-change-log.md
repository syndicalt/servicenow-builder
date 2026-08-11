# Sprint 240 Change Log - Classifier Gate Production Guard

## Summary

- Classifier gate production guard keeps exploratory model-routing bypasses out of hosted deployments.
- Added a production startup regression test for `JEDI_CLASSIFIER_GATE=false`.
- Updated runtime validation so production deployments reject the exploratory classifier-gate bypass before the API or worker starts.
- Documented that `JEDI_CLASSIFIER_GATE=false` is development-only.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_validate_runtime_settings_rejects_disabled_classifier_gate_in_production -q`
  - `1 passed`
- `python3 -m pytest tests/test_project_docs.py -q`
  - `314 passed`
- `python3 -m ruff check src tests`
  - `All checks passed!`
- `python3 -m mypy src tests`
  - `Success: no issues found in 174 source files`
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`
  - `1588 passed, 93.92% coverage`
