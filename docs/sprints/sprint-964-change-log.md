# Sprint 964 Change Log - Retrieved Update Set handoff instance URL guard

## Summary

Hardened retrieved Update Set handoff URL construction so corrupted in-process `UpdateSetHandoffRequest.instance_url` values cannot execute custom string methods while handoff metadata is created.

`_update_set_url()` now accepts only an exact Python `str` instance URL before constructing the `sys_remote_update_set.do` review link. Non-string values and string subclasses fail closed with `retrieved Update Set handoff instance URL contains non-JSON value`.

## Security impact

- Retrieved Update Set handoff no longer calls `rstrip()` on untrusted instance URL objects.
- Corrupted instance URL values fail before story work-note formatting, returned handoff metadata, or downstream API serialization can execute custom string hooks.
- This guard runs after retrieved Update Set import because the URL needs the imported set sys_id, so failures at this boundary are post-import handoff metadata failures.

## Tests

- Added 1 failing-first retrieved Update Set handoff instance URL assertion: `test_create_update_set_handoff_rejects_instance_url_object_without_leak`.
- Added 1 project-doc assertion: `tests/test_project_docs.py::test_sprint_964_documents_handoff_instance_url_guard`.

## Verification

- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_instance_url_object_without_leak -q` failed before implementation because direct URL construction executed the hostile instance URL `rstrip()`.
- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_instance_url_object_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_imports_retrieved_update_set_and_links_story -q` - 2 passed.
- `pytest tests/test_update_set_handoff.py::test_create_update_set_handoff_rejects_instance_url_object_without_leak tests/test_update_set_handoff.py::test_create_update_set_handoff_imports_retrieved_update_set_and_links_story tests/test_project_docs.py::test_sprint_964_documents_handoff_instance_url_guard -q` - 3 passed.
- `pytest tests/test_update_set_handoff.py -q` - 42 passed.
- `pytest tests/test_project_docs.py -q` - 1037 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed with no issues in 203 source files.
- `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` - 3653 passed, total coverage 93.25%.
