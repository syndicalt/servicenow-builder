# Sprint 733 Change Log - Project config read cause boundary

## Scope

Hardened project TOML configuration loading diagnostics so local config read and decode failures do
not retain unsafe `ArtifactReadError` or `UnicodeDecodeError` instances as public `ConfigError`
causes.

## Tests First

- Added 2 failing-first project config read cause assertions:
  - `tests/test_config.py::test_load_config_regular_file_error_does_not_echo_config_path`
  - `tests/test_config.py::test_load_config_invalid_utf8_error_does_not_echo_config_path_or_bytes`
- Initial failures proved the public `ConfigError` retained unsafe causes for:
  - `client_secret=config-link-secret.toml` symlinked config file rejection.
  - `client_secret=config-utf8-secret.toml` invalid UTF-8 config file rejection.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_733_documents_project_config_read_cause_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Suppressed original `ArtifactReadError` causes when symlinked or non-regular project TOML files
  are rejected.
- Suppressed original `UnicodeDecodeError` causes when project TOML files contain invalid UTF-8.
- Preserved the existing fixed diagnostics:
  - `project_config_must_be_regular_file`
  - `project_config_invalid_utf8`
- Documented the project config read cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_config.py -q -k "regular_file or invalid_utf8"` failed first with
  2 failures.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_733` failed first with 1 failure.
- `python3 -m pytest tests/test_config.py -q -k "regular_file or invalid_utf8 or accepts_valid_config"`
  passed with 2 tests and 13 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_733` passed with 1 test and 806
  deselected.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_config.py -q` passed with 15 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3060 tests and 93.33% total coverage.
