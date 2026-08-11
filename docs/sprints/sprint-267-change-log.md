# Sprint 267 Change Log - Bounded CLI JSON Input

## Summary

- Added a shared CLI JSON input limit of 10 MiB.
- Replaced CLI JSON `Path.read_text()` loaders with a bounded binary read that rejects oversized input before decode and JSON parsing.
- Routed provider responses, artifact handoff jobs, implementation candidate jobs, sample stories, handoff reports, and writeback job files through the bounded loader.
- Added failing regressions proving object and list JSON loaders reject oversized files without calling `Path.read_text()`.
- Documented the CLI JSON input cap in the operator guide.

## Verification

- `python3 -m pytest tests/test_cli_io.py::test_load_json_object_rejects_oversized_input_without_read_text tests/test_cli_io.py::test_load_json_list_rejects_oversized_input_without_read_text -q` - 2 tests failed before implementation because the loaders called `Path.read_text()`.
- `python3 -m pytest tests/test_cli_io.py tests/test_cli.py::test_cli_attach_delivery_artifacts_hash_check_uses_streaming_read tests/test_writeback_audit.py::test_lifecycle_manifest_hashes_artifacts_without_whole_file_read -q` - 4 passed.
- `python3 -m ruff check src/jedi_devproject/cli_io.py src/jedi_devproject/cli_pipeline.py src/jedi_devproject/writeback_orchestration.py tests/test_cli_io.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/cli_io.py src/jedi_devproject/cli_pipeline.py src/jedi_devproject/writeback_orchestration.py tests/test_cli_io.py` - success: no issues found in 4 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 175 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 341 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1669 passed, total coverage 94.00%.
