# Sprint 158 Change Log

## Summary

- Added runtime setting `JEDI_CLASSIFIER_GATE=<true|false>`.
- Kept the default as `true`, preserving the normal fail-closed classifier behavior for unknown and unsupported ServiceNow surfaces.
- When `JEDI_CLASSIFIER_GATE=false`, model fulfillment can call the provider for exploratory structured reasoning even when the classifier outcome is not `automated_build` or live instance context is missing.
- Preserved the review boundary: classifier-gate bypass candidates remain `Manual Build` / `Human Review Required` and do not create retrieved Update Set handoffs.

## Verification

- `pytest tests/test_model_fulfillment.py::test_model_fulfillment_can_disable_classifier_gate_for_exploratory_reasoning tests/test_runtime.py::test_load_runtime_settings_accepts_env_file tests/test_runtime.py::test_load_runtime_settings_defaults_classifier_gate_enabled -q`
