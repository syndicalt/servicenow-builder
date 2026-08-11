# Sprint 986 Change Log - Model fulfillment story fetch guard

## Summary

Hardened model-candidate fulfillment story lookup so malformed ServiceNow story collections cannot execute truthiness, indexing, enrichment, or model hooks before implementation packet generation, live context discovery, provider invocation, retrieved Update Set handoff, or story writeback.

`model_candidate_fulfillment_handler()` now routes `fetch_stories()` results through `_model_fulfillment_stories()`. The helper accepts only exact Python lists containing exact `Story` records and fails closed with `model fulfillment stories contain non-JSON value`.

## Security impact

- Malformed story collections fail before truthiness hooks, story-not-found handling, indexing, enrichment, capability analysis, ServiceNow context fetches, provider calls, handoff creation, story mutation, or artifact-return construction.
- Malformed story items fail before model-subclass hooks can run during enrichment.
- Diagnostics do not include collection type names, item type names, hook output, or credential-like fragments.
- Provider calls, ServiceNow table fetches beyond the initial story lookup, Update Set imports, and story mutations do not occur for malformed story fetch data.

## Tests

- Added 1 failing-first model fulfillment story collection assertion: `test_model_candidate_handler_rejects_story_collection_subclass_without_leak`.
- Added 1 model fulfillment story item assertion: `test_model_candidate_handler_rejects_story_item_subclass_without_leak`.
- Added 1 project-doc assertion: `tests/test_project_docs.py::test_sprint_986_documents_model_fulfillment_story_fetch_guard`.

## Verification

- `pytest tests/test_model_fulfillment.py::test_model_candidate_handler_rejects_story_collection_subclass_without_leak tests/test_model_fulfillment.py::test_model_candidate_handler_rejects_story_item_subclass_without_leak -q` failed before implementation because malformed story data executed collection truthiness and enrichment model-copy hooks.
- `pytest tests/test_model_fulfillment.py::test_model_candidate_handler_rejects_story_collection_subclass_without_leak tests/test_model_fulfillment.py::test_model_candidate_handler_rejects_story_item_subclass_without_leak tests/test_project_docs.py::test_sprint_986_documents_model_fulfillment_story_fetch_guard -q` - 3 passed.
- `pytest tests/test_model_fulfillment.py -q` - 39 passed.
- `pytest tests/test_project_docs.py -q` - 1059 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` - 3715 passed, 93.28% coverage.
