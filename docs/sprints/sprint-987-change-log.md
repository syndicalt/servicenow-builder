# Sprint 987 Change Log - Runtime failure notifier story collection guard

## Summary

Hardened runtime ServiceNow failure-notifier story lookup so malformed `fetch_stories()` collections cannot execute truthiness or indexing hooks while the worker writes failed-fulfillment status and work notes back to the originating story.

`_servicenow_failure_notifier()` now routes fetched story collections through `_failure_notifier_stories()`. The helper accepts only exact Python lists and fails closed with the existing `story lookup result is unsafe` diagnostic.

## Security impact

- Malformed story collections fail before truthiness hooks, story-not-found handling, indexing, Draft-state lookup, ServiceNow mutation, or failed-story work-note construction.
- Alternate iterables such as tuples are rejected instead of being accepted implicitly.
- Diagnostics do not include collection type names, hook output, or credential-like fragments.
- The existing found-story `sys_id` validation remains the item-level boundary, preserving compatibility with typed ServiceNow stories and existing safe lightweight story records.

## Tests

- Added 1 failing-first failure-notifier story collection subclass assertion: `test_servicenow_failure_notifier_rejects_story_collection_subclass_without_leak`.
- Added 1 failure-notifier alternate iterable assertion: `test_servicenow_failure_notifier_rejects_alternate_story_iterable`.
- Added 1 project-doc assertion: `tests/test_project_docs.py::test_sprint_987_documents_runtime_failure_notifier_story_collection_guard`.

## Verification

- `pytest tests/test_runtime.py::test_servicenow_failure_notifier_rejects_story_collection_subclass_without_leak tests/test_runtime.py::test_servicenow_failure_notifier_rejects_alternate_story_iterable -q` failed before implementation because malformed story collection data leaked a collection hook diagnostic and tuple results were accepted.
- `pytest tests/test_runtime.py::test_servicenow_failure_notifier_rejects_story_collection_subclass_without_leak tests/test_runtime.py::test_servicenow_failure_notifier_rejects_alternate_story_iterable tests/test_project_docs.py::test_sprint_987_documents_runtime_failure_notifier_story_collection_guard -q` - 3 passed.
- `pytest tests/test_runtime.py -q` - 426 passed.
- `pytest tests/test_project_docs.py -q` - 1060 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` - 3718 passed, 93.29% coverage.
