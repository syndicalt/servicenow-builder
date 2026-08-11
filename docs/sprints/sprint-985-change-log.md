# Sprint 985 Change Log - Intake feedback story fetch guard

## Summary

Hardened fulfillment-handler intake feedback story lookup so malformed ServiceNow story collections cannot execute truthiness, indexing, enrichment, or model hooks while the fail-open intake assessment prepares requester feedback.

`_assess_intake_feedback()` now routes `fetch_stories()` results through `_intake_stories()`. The helper accepts only exact Python lists containing exact `Story` records and fails closed with `intake story fetch contains non-JSON value`.

## Security impact

- Malformed intake story collections fail before truthiness hooks, story-not-found handling, indexing, enrichment, capability analysis, work-note planning, ServiceNow mutation, or feedback artifact writing.
- Malformed intake story items fail before model-subclass hooks can run during enrichment.
- Diagnostics do not include collection type names, item type names, hook output, or credential-like fragments.
- Intake feedback remains fail-open for fulfillment progress, but the logged exception is a sanitized fixed diagnostic instead of caller-controlled exception text.

## Tests

- Added 1 failing-first intake feedback story collection assertion: `test_intake_feedback_rejects_story_collection_subclass_without_log_leak`.
- Added 1 intake feedback story item assertion: `test_intake_feedback_rejects_story_item_subclass_without_log_leak`.
- Added 1 project-doc assertion: `tests/test_project_docs.py::test_sprint_985_documents_intake_feedback_story_fetch_guard`.

## Verification

- `pytest tests/test_fulfillment_handler.py::test_intake_feedback_rejects_story_collection_subclass_without_log_leak tests/test_fulfillment_handler.py::test_intake_feedback_rejects_story_item_subclass_without_log_leak -q` failed before implementation because malformed intake story data leaked collection and model-copy hook diagnostics into fulfillment-handler logs.
- `pytest tests/test_fulfillment_handler.py::test_intake_feedback_rejects_story_collection_subclass_without_log_leak tests/test_fulfillment_handler.py::test_intake_feedback_rejects_story_item_subclass_without_log_leak tests/test_project_docs.py::test_sprint_985_documents_intake_feedback_story_fetch_guard -q` - 3 passed.
- `pytest tests/test_fulfillment_handler.py -q` - 18 passed.
- `pytest tests/test_project_docs.py -q` - 1058 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` - 3712 passed, 93.28% coverage.
