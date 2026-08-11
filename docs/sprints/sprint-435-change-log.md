# Sprint 435 Change Log

## Local input loader non-reflective path diagnostics

Hardened local JSON and project TOML input loaders so low-level size and regular-file failures no longer echo raw operator-supplied filesystem paths. Prior diagnostics for `_read_bounded_json_bytes()` and `_read_bounded_config_text()` included the input path in `json_input_too_large`, `json_input_must_be_regular_file`, `project_config_too_large`, and `project_config_must_be_regular_file` errors.

Those paths can contain copied credentials, query strings, tenant identifiers, or other sensitive fragments. The loaders now preserve stable reason codes and configured byte limits without embedding the filename or absolute path in the exception message. Higher-level CLI rendering still applies redaction, but these lower-level validation errors no longer require redaction to avoid path leakage.

## Verification

- Added 4 failing-first tests covering oversized and symlinked JSON/config inputs with secret-bearing filenames.
- `python3 -m pytest tests/test_cli_io.py tests/test_config.py -q -k "does_not_echo"`: failed before implementation because the exception diagnostics included `json-loader-secret`, `json-link-secret`, `config-loader-secret`, and `config-link-secret`.
- `python3 -m pytest tests/test_cli_io.py tests/test_config.py -q -k "does_not_echo or oversized_input_without_read_text or symlinked"`: 9 tests passed.
- `python3 -m pytest tests/test_cli.py tests/test_cli_io.py tests/test_config.py -q -k "redacts_invalid_input_path_details or redacts_invalid_spec_path_details or does_not_echo or oversized_input_without_read_text or symlinked"`: 11 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 193 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 509 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2293 total tests passed at 93.96% coverage.
