# Sprint 633 Change Log

## Model fulfillment required-surface exact-string boundary

Sprint 633 continued production hardening by tightening `_required_surfaces_for_assessment()`, the model-fulfillment routing helper that turns capability-analysis `required_instance_context` into live ServiceNow surface retrieval overrides. The previous path called `str()` on every required-surface entry, so malformed in-process routing metadata could execute custom conversion or leak fragments while the worker decided which context gates had to be satisfied before model execution.

Required-surface overrides now keep only exact string surface names. Malformed, string-subclass, non-string, or unstringifiable entries are skipped without coercion. Existing public-documentation augmentation remains unchanged.

Verification:

- Added 1 failing-first model fulfillment test proving hostile required-surface entries executed before implementation.
- `python3 -m pytest tests/test_model_fulfillment.py::test_required_surfaces_skip_malformed_context_entries_without_coercion -q`: failed before implementation with the hostile `required-surface-secret` exception.
- `python3 -m pytest tests/test_model_fulfillment.py::test_required_surfaces_skip_malformed_context_entries_without_coercion tests/test_model_fulfillment.py::test_surface_context_story_text_skips_malformed_story_fields_without_coercion tests/test_model_fulfillment.py::test_model_candidate_handler_blocks_model_when_required_surface_context_missing -q`: 3 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 707 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed with no issues in 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2755 tests passed at 93.08% coverage.
