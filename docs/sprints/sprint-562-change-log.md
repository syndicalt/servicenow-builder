# Sprint 562 Change Log

## ServiceNow story additional-context length guard

Sprint 562 continued production hardening by bounding ServiceNow AI additional-context fields before `Story` model construction. `_story_from_record()` already rejected non-string story response text before constructing `Story`, but optional AI operational reference fields such as `u_ai_build_reference` and `u_ai_candidate_artifact` could be arbitrarily large while still being accepted into `Story.additional_context`.

AI additional-context validation now rejects values longer than 1024 characters before `Story.additional_context` construction, downstream packet generation, writeback orchestration checks, or model-provider context assembly. Oversized additional-context values fail with the fixed `ServiceNow API story response field is unsafe` diagnostic. The diagnostic does not echo submitted context values, story values, object representations, or credential-like payloads.

This intentionally does not cap user-authored story descriptions or acceptance criteria in this sprint; those fields need a separate product decision because they may legitimately carry long requirements text.

Verification:

- Added 1 failing-first ServiceNow story additional-context length test proving a 1025-character `u_ai_build_reference` was accepted into `Story.additional_context` before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_oversized_story_additional_context -q`: failed before implementation because the oversized additional-context value did not raise `ServiceNowApiError`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_oversized_story_additional_context tests/test_servicenow.py::test_servicenow_client_fetch_stories_allows_explicit_query tests/test_servicenow.py::test_servicenow_client_rejects_non_string_story_response_text_without_stringifying tests/test_servicenow.py::test_servicenow_client_rejects_non_numeric_story_points_without_stringifying -q`: 4 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 164 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 636 passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2595 passed, 93.42% total coverage.
