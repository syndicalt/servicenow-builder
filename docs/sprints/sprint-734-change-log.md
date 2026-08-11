# Sprint 734 Change Log - CLI JSON input cause boundary

## Scope

Hardened shared CLI JSON input diagnostics so local JSON read, decode, and parser failures do not
retain unsafe low-level exception instances as public `ValueError` causes.

## Tests First

- Added 3 failing-first CLI JSON input cause assertions:
  - `tests/test_cli_io.py::test_load_json_object_regular_file_error_does_not_echo_input_path`
  - `tests/test_cli_io.py::test_load_json_object_invalid_utf8_error_does_not_echo_input_path_or_bytes`
  - `tests/test_cli_io.py::test_load_json_object_rejects_non_finite_json_without_payload_leak`
- Initial failures proved the public `ValueError` retained unsafe causes for:
  - `client_secret=json-link-secret.json` symlinked JSON input rejection.
  - `client_secret=json-utf8-secret.json` invalid UTF-8 JSON input rejection.
  - `client_secret=json-nan-secret.json` non-finite JSON parser rejection.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_734_documents_cli_json_input_cause_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Suppressed original `ArtifactReadError` causes when symlinked or non-regular CLI JSON inputs are
  rejected.
- Suppressed original `UnicodeDecodeError` causes when CLI JSON inputs contain invalid UTF-8.
- Suppressed original JSON parser causes when malformed or non-finite JSON input is rejected.
- Preserved the existing fixed diagnostics:
  - `json_input_must_be_regular_file`
  - `json_input_invalid_utf8`
  - `json_input_invalid_json`
- Documented the CLI JSON input cause boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_cli_io.py -q -k "regular_file_error or invalid_utf8 or non_finite_json"`
  failed first with 3 failures.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_734` failed first with 1 failure.
- `python3 -m pytest tests/test_cli_io.py -q -k "regular_file_error or invalid_utf8 or non_finite_json"`
  passed with 3 tests and 9 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_734` passed with 1 test and 807
  deselected.
- `ruff check src tests` passed.
- `mypy src tests` passed with no issues in 197 source files.
- `python3 -m pytest tests/test_cli_io.py -q` passed with 12 tests.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with
  3061 tests and 93.33% total coverage.
