# Sprint 962 Change Log - Retrieved Update Set handoff reviewer-note collection guard

## Summary

Hardened retrieved Update Set reviewer-note description rendering so corrupted in-process `UpdateSetCandidate.reviewer_notes` collections cannot execute custom truthiness or iteration hooks while the review handoff XML is created.

`_reviewer_note_lines()` now consumes reviewer notes through `_reviewer_notes()`. The guard accepts only an exact Python `list` for `reviewer_notes`. List subclasses, alternate iterables, and corrupted model-copy payloads fail closed with `retrieved Update Set handoff reviewer notes contain non-JSON value`.

## Security impact

- Retrieved Update Set description rendering no longer calls `bool()` on untrusted reviewer-note collections.
- Retrieved Update Set description rendering no longer iterates list subclasses or alternate iterable reviewer-note containers.
- Individual note values continue through `safe_work_note_value()`, preserving the existing non-string note diagnostic behavior.

## Tests

- Added 1 failing-first retrieved Update Set handoff reviewer-note collection assertion: `test_create_update_set_handoff_rejects_reviewer_note_collection_subclass_without_leak`.
- Added 1 project-doc assertion: `tests/test_project_docs.py::test_sprint_962_documents_handoff_reviewer_note_collection_guard`.

## Verification

- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_reviewer_note_collection_subclass_without_leak -q` failed before implementation because direct truthiness checking executed the hostile reviewer-note collection `__bool__`.
- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_reviewer_note_collection_subclass_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_sanitizes_reviewer_note_without_stringifying tests/test_update_set_handoff.py::test_create_update_set_handoff_imports_retrieved_update_set_and_links_story -q` - 3 passed.
- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_reviewer_note_collection_subclass_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_sanitizes_reviewer_note_without_stringifying tests/test_update_set_handoff.py::test_create_update_set_handoff_imports_retrieved_update_set_and_links_story tests/test_project_docs.py::test_sprint_962_documents_handoff_reviewer_note_collection_guard -q` - 4 passed.
- `pytest tests/test_update_set_handoff.py -q` - 40 passed.
- `pytest tests/test_project_docs.py -q` - 1035 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed with no issues in 203 source files.
- `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` - 3649 passed, total coverage 93.24%.
