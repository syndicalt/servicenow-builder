# Sprint 963 Change Log - Retrieved Update Set handoff story-number name guard

## Summary

Hardened retrieved Update Set name construction so corrupted in-process `UpdateSetHandoffRequest.story_number` values cannot execute custom string hooks while the ServiceNow review handoff is created.

`_update_set_name()` now accepts only an exact Python `str` story number before constructing `JEDI <story number> - AI Candidate`. Non-string values and string subclasses fail closed with `retrieved Update Set handoff story number contains non-JSON value`.

## Security impact

- Retrieved Update Set handoff no longer directly interpolates untrusted story-number objects.
- Corrupted story-number values fail before Update Set name construction, XML serialization, ServiceNow import, work-note formatting, or returned handoff metadata.
- The guard preserves normal exact-string story-number handling for validated runtime requests.

## Tests

- Added 1 failing-first retrieved Update Set handoff story-number assertion: `test_create_update_set_handoff_rejects_story_number_object_without_leak`.
- Added 1 project-doc assertion: `tests/test_project_docs.py::test_sprint_963_documents_handoff_story_number_name_guard`.

## Verification

- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_story_number_object_without_leak -q` failed before implementation because direct Update Set name formatting executed the hostile story-number `__str__`.
- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_story_number_object_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_imports_retrieved_update_set_and_links_story -q` - 2 passed.
- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_story_number_object_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_imports_retrieved_update_set_and_links_story tests/test_project_docs.py::test_sprint_963_documents_handoff_story_number_name_guard -q` - 3 passed.
- `pytest tests/test_update_set_handoff.py -q` - 41 passed.
- `pytest tests/test_project_docs.py -q` - 1036 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed with no issues in 203 source files.
- `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` - 3651 passed, total coverage 93.25%.
