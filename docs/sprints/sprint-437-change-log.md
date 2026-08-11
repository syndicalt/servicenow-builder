# Sprint 437 Change Log

## Local input loader invalid UTF-8 diagnostics

Hardened local JSON and project TOML input loaders so invalid UTF-8 bytes fail with stable, non-reflective reason codes instead of raw `UnicodeDecodeError` diagnostics. Prior behavior let `payload_bytes.decode("utf-8")` and `payload.decode("utf-8")` exceptions escape from the shared CLI JSON loader and project config loader.

The JSON loader now raises `json_input_invalid_utf8`, and the project config loader raises `project_config_invalid_utf8`. These diagnostics do not include the input path, decoded payload fragments, byte positions, or submitted key names. Size and regular-file controls continue to run before decode.

## Verification

- Added 2 failing-first tests covering invalid UTF-8 JSON/config inputs with secret-bearing filenames and credential-like payload keys.
- `python3 -m pytest tests/test_cli_io.py tests/test_config.py -q -k "invalid_utf8"`: failed before implementation because raw `UnicodeDecodeError` diagnostics escaped from the loaders.
- `python3 -m pytest tests/test_cli_io.py tests/test_config.py -q -k "invalid_utf8 or does_not_echo or oversized_input_without_read_text or symlinked"`: 11 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 193 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 511 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2298 total tests passed at 93.96% coverage.
