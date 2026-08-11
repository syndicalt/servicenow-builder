# Sprint 969 Change Log - Retrieved Update Set handoff artifact reference guard

## Summary

Hardened retrieved Update Set handoff artifact references so corrupted in-process `UpdateSetHandoffRequest.candidate_artifact_ref` values cannot reach structured ServiceNow story writeback.

`create_update_set_handoff()` now validates `candidate_artifact_ref` through `_handoff_artifact_ref()` before candidate routing or retrieved Update Set import. The helper accepts only exact Python strings. Non-string values and string subclasses fail closed with `retrieved Update Set handoff artifact reference contains non-JSON value`.

## Security impact

- Malformed candidate artifact references fail before customer-update generation, XML serialization, ServiceNow import, structured story field updates, or work-note formatting.
- The handoff no longer passes corrupted artifact-reference objects into ServiceNow writeback payloads.
- Normal validated runtime requests continue to write exact artifact reference strings.

## Tests

- Added 1 failing-first retrieved Update Set handoff artifact reference assertion: `test_create_update_set_handoff_rejects_artifact_ref_object_without_leak`.
- Added 1 project-doc assertion: `tests/test_project_docs.py::test_sprint_969_documents_handoff_artifact_ref_guard`.

## Verification

- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_artifact_ref_object_without_leak -q` failed before implementation because malformed artifact references were accepted.
- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_artifact_ref_object_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_imports_retrieved_update_set_and_links_story -q` - 2 passed.
- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_sanitizes_description_header_without_stringifying tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_artifact_ref_object_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_imports_retrieved_update_set_and_links_story -q` - 3 passed.
- `pytest tests/test_update_set_handoff.py -q` - 47 passed.
- `pytest tests/test_project_docs.py -q` - 1042 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` - 3663 passed, total coverage 93.23%.
