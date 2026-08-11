# Sprint 342 Change Log

Scope: Production hardening - CLI JSON input regular-file enforcement.

## Summary

- CLI JSON input loading now uses the shared descriptor-safe regular-file reader instead of direct `Path.open()`.
- Operator-supplied JSON files reject symlinked paths and non-regular filesystem entries with `json_input_must_be_regular_file`.
- The existing 10 MiB JSON input cap and redacted CLI diagnostics are preserved.
- This covers provider responses, lifecycle specs, handoff reports, handoff job files, sample stories, implementation candidate jobs, and writeback job files through the shared `load_json_payload()` path.

## Verification

- `python3 -m pytest tests/test_cli_io.py::test_load_json_object_rejects_symlinked_input tests/test_cli_io.py::test_load_json_list_rejects_symlinked_input -q` - 2 tests failed before implementation because symlinked JSON inputs were accepted.
- `python3 -m pytest tests/test_cli_io.py -q` - 4 passed after implementation.
- `python3 -m pytest tests/test_cli.py::test_cli_process_external_build_result_redacts_invalid_input_path_details tests/test_cli.py::test_cli_apply_lifecycle_webhook_redacts_invalid_spec_path_details -q` - 2 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_three_hundred_forty_two_documents_cli_json_regular_file_input tests/test_cli_io.py tests/test_cli.py::test_cli_process_external_build_result_redacts_invalid_input_path_details tests/test_cli.py::test_cli_apply_lifecycle_webhook_redacts_invalid_spec_path_details -q` - 7 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 187 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 416 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1993 passed, total coverage 93.99%.
