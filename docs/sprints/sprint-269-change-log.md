# Sprint 269 Change Log - Bounded Project Config TOML Input

## Summary

- Added a 1 MiB project config TOML input cap.
- Replaced project config `Path.read_text()` parsing with a bounded binary read before UTF-8 decode and TOML parsing.
- Oversized project config files now fail closed with `project_config_too_large` before required-setting validation.
- Preserved existing behavior for required setting validation and accepted `servicenow_instance_url`, `artifact_dir`, and `target_boundary` parsing.
- Added a failing regression proving oversized TOML input is rejected without calling `Path.read_text()`.
- Documented the project config TOML input cap in the operator guide.

## Verification

- `python3 -m pytest tests/test_config.py::test_load_config_rejects_oversized_toml_without_whole_file_text_read -q` - 1 test failed before implementation because the loader called `Path.read_text()`.
- `python3 -m pytest tests/test_config.py -q` - 3 passed.
- `python3 -m pytest tests/test_config.py tests/test_project_docs.py::test_sprint_two_hundred_sixty_nine_documents_bounded_project_config_toml -q` - 4 passed.
- `python3 -m ruff check src/jedi_devproject/config.py tests/test_config.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/config.py tests/test_config.py tests/test_project_docs.py` - success: no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 175 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 343 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1673 passed, total coverage 94.01%.
