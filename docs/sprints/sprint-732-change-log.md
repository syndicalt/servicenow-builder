# Sprint 732 Change Log - ServiceNow dotenv read cause boundary

## Scope

Hardened ServiceNow dotenv loading diagnostics so local env file read and decode failures do not
retain unsafe `ArtifactReadError` or `UnicodeDecodeError` instances as public `ValueError` causes.

## Tests First

- Added 2 failing-first ServiceNow dotenv read cause assertions:
  - `tests/test_servicenow.py::test_load_dotenv_values_regular_file_error_does_not_echo_env_path`
  - `tests/test_servicenow.py::test_load_dotenv_values_invalid_utf8_error_does_not_echo_env_path_or_bytes`
- Initial failures proved the public `ValueError` retained unsafe causes for:
  - `client_secret=dotenv-link-secret.env` symlinked env file rejection.
  - `client_secret=dotenv-utf8-secret.env` invalid UTF-8 env file rejection.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_732_documents_dotenv_read_cause_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Suppressed original `ArtifactReadError` causes when symlinked or non-regular dotenv files are
  rejected.
- Suppressed original `UnicodeDecodeError` causes when dotenv files contain invalid UTF-8.
- Preserved the existing fixed diagnostics:
  - `dotenv_must_be_regular_file`
  - `dotenv_invalid_utf8`
- Documented the ServiceNow dotenv read cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "regular_file_error_does_not_echo_env_path or invalid_utf8_error_does_not_echo_env_path_or_bytes"`
  failed first with 2 failures.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_732` failed first with 1 failure.
- `python3 -m pytest tests/test_servicenow.py -q -k "regular_file_error_does_not_echo_env_path or invalid_utf8_error_does_not_echo_env_path_or_bytes or rejects_symlinked_env_file or rejects_oversized_env"`
  passed with 4 tests and 284 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_732` passed with 1 test and 805
  deselected.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_servicenow.py -q` passed with 288 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3059 tests and 93.33% total coverage.
