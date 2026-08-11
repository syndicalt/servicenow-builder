# Sprint 632 Change Log

## Model fulfillment story text exact-string context boundary

Sprint 632 continued production hardening by tightening `_surface_context_and_rags_for_story()`, the model-fulfillment boundary that builds story text for live ServiceNow surface discovery and optional public-documentation retrieval. The previous path called `str()` on `short_description`, `description`, and `acceptance_criteria` values from a generic story object, so malformed in-process story fields could execute custom conversion or leak text while the worker prepared model context.

Story text construction now uses `_story_text_for_surface_context()`. It reads `short_description`, `description`, and `acceptance_criteria` only when each value is a non-empty exact string. Missing, non-string, string-subclass, or unstringifiable values are skipped without coercion before context discovery or public-doc query planning.

Verification:

- Added 1 failing-first model fulfillment test proving hostile story text values executed before implementation.
- `python3 -m pytest tests/test_model_fulfillment.py::test_surface_context_story_text_skips_malformed_story_fields_without_coercion -q`: failed before implementation with the hostile `story-text-secret` exception.
- `python3 -m pytest tests/test_model_fulfillment.py::test_surface_context_story_text_skips_malformed_story_fields_without_coercion tests/test_model_fulfillment.py::test_model_candidate_handler_adds_live_public_docs_to_packet tests/test_model_fulfillment.py::test_model_candidate_handler_skips_provider_when_required_public_docs_missing -q`: 3 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 706 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed with no issues in 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2753 tests passed at 93.08% coverage.
