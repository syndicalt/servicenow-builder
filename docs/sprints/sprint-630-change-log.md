# Sprint 630 Change Log

## Artifact handoff CLI exact story-number boundary

Sprint 630 continued production hardening by tightening the CLI boundary for artifact handoff reports. `write-artifact-handoff-summary` previously read `report["story_number"]` with `str()` before validating report shape, so a malformed local report could be accepted as a story identifier or crash later while building the work note. `attach-delivery-artifacts` already failed closed through delivery-job validation, but it still read the story number before that validator ran.

Both CLI commands now call `_handoff_report_story_number()` before story-specific output, confirmation checks, ServiceNow query construction, client creation, or attachment planning. The helper accepts only non-empty exact strings and raises the stable `artifact_handoff_report_invalid` reason for missing, empty, numeric, or otherwise malformed identifiers.

Verification:

- Added 2 failing-first CLI tests covering malformed handoff report story numbers for summary writing and delivery attachment planning.
- `python3 -m pytest tests/test_cli.py::test_cli_write_artifact_handoff_summary_rejects_non_string_story_number tests/test_cli.py::test_cli_attach_delivery_artifacts_rejects_non_string_story_number -q`: failed before implementation because summary writing accepted numeric story numbers.
- `python3 -m pytest tests/test_cli.py::test_cli_write_artifact_handoff_summary_rejects_non_string_story_number tests/test_cli.py::test_cli_attach_delivery_artifacts_rejects_non_string_story_number tests/test_cli.py::test_cli_write_artifact_handoff_summary_dry_run_does_not_mutate tests/test_cli.py::test_cli_attach_delivery_artifacts_dry_run_does_not_attach -q`: 4 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 704 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed with no issues in 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2749 tests passed at 93.08% coverage.
