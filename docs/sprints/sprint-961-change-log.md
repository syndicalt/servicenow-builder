# Sprint 961 Change Log - Retrieved Update Set handoff changes collection guard

## Summary

Hardened retrieved Update Set handoff candidate-change access so corrupted in-process `UpdateSetCandidate.changes` values cannot execute custom truthiness or iteration hooks while customer updates are routed or review descriptions are serialized.

`_customer_updates_for_candidate()` and `_change_summary_lines()` now consume candidate changes through `_candidate_changes()`. The guard accepts only an exact Python `list` containing exact `CandidateChange` records. List subclasses, alternate iterables, malformed entries, and corrupted model-copy payloads fail closed with `retrieved Update Set handoff changes contain non-JSON value`.

## Security impact

- Retrieved Update Set handoff routing no longer calls `bool()` on untrusted candidate change containers.
- Retrieved Update Set handoff routing and description summaries no longer iterate list subclasses or alternate iterable objects.
- Malformed candidate change entries fail before table routing, deterministic customer-update generation, or description summary rendering.

## Tests

- Added 1 failing-first retrieved Update Set handoff changes collection assertion: `test_create_update_set_handoff_rejects_changes_collection_subclass_without_leak`.
- Added 1 project-doc assertion: `tests/test_project_docs.py::test_sprint_961_documents_handoff_changes_collection_guard`.

## Verification

- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_changes_collection_subclass_without_leak -q` failed before implementation because direct truthiness checking executed the hostile changes collection `__bool__`.
- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_changes_collection_subclass_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_imports_retrieved_update_set_and_links_story -q` - 2 passed.
- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_changes_collection_subclass_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_imports_retrieved_update_set_and_links_story tests/test_project_docs.py::test_sprint_961_documents_handoff_changes_collection_guard -q` - 3 passed.
- `pytest tests/test_update_set_handoff.py -q` - 39 passed.
- `pytest tests/test_project_docs.py -q` - 1034 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed with no issues in 203 source files.
- `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` - 3647 passed, total coverage 93.24%.
