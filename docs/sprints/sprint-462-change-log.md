# Sprint 462 Change Log

## CLI JSON input non-finite number rejection

Hardened shared CLI JSON input loading so local artifact files containing non-standard JSON numeric
constants such as `NaN`, `Infinity`, or `-Infinity` cannot enter offline build, writeback, or report
commands as Python float values. Python `json.loads()` accepts those constants by default, so a
malformed local provider response, implementation candidate batch, lifecycle spec, or handoff file
could previously bypass the file-size and UTF-8 gates and fail later as ordinary data.

`load_json_payload()` now parses with strict JSON numeric handling and maps malformed JSON syntax and
non-finite constants to the fixed `json_input_invalid_json` reason code. The diagnostic does not echo
local file paths, submitted field names, credential-like keys, or payload values. Existing
regular-file, symlink, size, UTF-8, object-shape, and list-shape diagnostics are unchanged.

## Verification

- Added 1 failing-first CLI JSON input test covering non-finite JSON rejection without path,
  field-name, credential-key, or payload-value reflection.
- `python3 -m pytest tests/test_cli_io.py::test_load_json_object_rejects_non_finite_json_without_payload_leak -q`:
  failed before implementation because `NaN` was accepted as a parsed float.
- `python3 -m pytest tests/test_cli_io.py -q`: 11 tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 536 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`:
  2365 total tests passed at 93.83% coverage.
