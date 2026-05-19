# Sprint 156 Change Log

## Summary

- Added a structured `context_dossier` to implementation packets so the model receives story data, capability assessment, context sufficiency, live instance context, surface context, builder maturity, and read-only XML shape references in one model-facing object.
- Changed the model output contract to `structured_candidate_change_only`; raw XML fields or raw Update Set XML content in model responses now fail validation.
- Removed the deterministic form-section candidate bypass. Form-section stories now call the model for structured reasoning when context is sufficient, then route to human review because the form-section retrieved Update Set builder is below the automated handoff maturity threshold.
- Restricted retrieved Update Set handoff to mature deterministic dictionary/form changes. Other structured candidates are preserved as artifacts and write human-review feedback instead of importing immature XML.

## Verification

- `pytest tests/test_implementation_packet.py tests/test_update_set_handoff.py tests/test_model_fulfillment.py tests/test_runtime.py tests/test_project_docs.py -q`
