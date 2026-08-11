# Sprint 250 Change Log - Runtime Boolean Parsing Hygiene

## Summary

- Runtime boolean parsing hygiene prevents typoed environment values from silently disabling or enabling production controls.
- Added a parameterized runtime settings regression test for malformed values across `JEDI_BUILD_CLAIM_APPLY`, `JEDI_STRICT_TRANSPORT_SECURITY_ENABLED`, `JEDI_ALERT_WEBHOOK_ENABLED`, `JEDI_UPDATE_SET_APPLY`, and `JEDI_CLASSIFIER_GATE`.
- Replaced loose truthy parsing in `load_runtime_settings()` with strict boolean parsing that accepts only `true`, `false`, `1`, `0`, `yes`, `no`, `on`, or `off`.
- Documented that malformed runtime boolean values fail settings loading instead of being silently treated as false.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_load_runtime_settings_rejects_malformed_runtime_boolean_values tests/test_runtime.py::test_load_runtime_settings_defaults_classifier_gate_enabled tests/test_runtime.py::test_load_runtime_settings_accepts_env_file tests/test_runtime.py::test_load_runtime_settings_reads_strict_transport_security_config tests/test_runtime.py::test_load_runtime_settings_reads_alert_webhook_config tests/test_runtime.py::test_load_runtime_settings_reads_update_set_apply_controls -q`
  - `10 passed`
- `python3 -m ruff check src tests`
  - `All checks passed!`
- `python3 -m mypy src tests`
  - `Success: no issues found in 174 source files`
- `python3 -m pytest tests/test_project_docs.py -q`
  - `324 passed`
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`
  - `1612 passed`
  - `Total coverage: 93.95%`
