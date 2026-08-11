# Sprint 988 Change Log - Artifact handoff CLI story lookup guard

## Summary

Hardened artifact handoff CLI story lookup so malformed ServiceNow story collections cannot execute truthiness, indexing, or model hooks before work-note summary writeback or delivery attachment upload.

`write_artifact_handoff_summary_command()` and `attach_delivery_artifacts_command()` now route `fetch_stories()` results through `_cli_story_lookup_results()`. The helper accepts only exact Python lists containing exact `Story` records and fails closed with `story_lookup_result_unsafe`.

## Security impact

- Malformed story collections fail before truthiness hooks, story-not-found handling, indexing, work-note update, attachment upload, attachment audit writing, or story sys_id exposure.
- Malformed story items fail before model-subclass hooks can run.
- Diagnostics do not include collection type names, item type names, hook output, or credential-like fragments.
- Handoff summary writeback and delivery attachment apply both return fixed operator-facing reason codes without mutating ServiceNow.

## Tests

- Added 1 failing-first handoff summary story collection assertion: `test_cli_write_artifact_handoff_summary_rejects_story_collection_subclass_without_leak`.
- Added 1 delivery attachment story collection assertion: `test_cli_attach_delivery_artifacts_rejects_story_collection_subclass_without_leak`.
- Added 1 project-doc assertion: `tests/test_project_docs.py::test_sprint_988_documents_artifact_handoff_cli_story_lookup_guard`.

## Verification

- `pytest tests/test_cli.py::test_cli_write_artifact_handoff_summary_rejects_story_collection_subclass_without_leak tests/test_cli.py::test_cli_attach_delivery_artifacts_rejects_story_collection_subclass_without_leak -q` failed before implementation because malformed story collections executed truthiness hooks and leaked hook diagnostics before CLI commands could print a fixed reason.
- `pytest tests/test_cli.py::test_cli_write_artifact_handoff_summary_rejects_story_collection_subclass_without_leak tests/test_cli.py::test_cli_attach_delivery_artifacts_rejects_story_collection_subclass_without_leak tests/test_project_docs.py::test_sprint_988_documents_artifact_handoff_cli_story_lookup_guard -q` - 3 passed.
- `pytest tests/test_cli.py -q` - 75 passed.
- `pytest tests/test_project_docs.py -q` - 1061 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` - 3721 passed, 93.28% coverage.
