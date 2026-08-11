# Sprint 438 Change Log

## Dotenv loader non-reflective path and UTF-8 diagnostics

Hardened local `.env` credential loading so size, regular-file, and UTF-8 decode failures no longer echo raw filesystem paths or raw decoder diagnostics. Prior behavior included the input path in `dotenv_input_too_large` and `dotenv_must_be_regular_file`, and allowed raw `UnicodeDecodeError` text to escape when `.env` bytes were not valid UTF-8.

The `.env` loader now preserves stable reason codes without reflecting operator-controlled path fragments or credential-like payload keys:

- `dotenv_input_too_large`
- `dotenv_must_be_regular_file`
- `dotenv_invalid_utf8`

Size and regular-file checks still run before parsing credentials, and the oversized diagnostic keeps the configured byte limit without including the submitted path.

## Verification

- Added 3 failing-first tests covering oversized, symlinked, and invalid UTF-8 `.env` inputs with secret-bearing filenames or credential-like payload keys.
- `python3 -m pytest tests/test_servicenow.py -q -k "dotenv_values_oversized_error or dotenv_values_regular_file_error or dotenv_values_invalid_utf8"`: failed before implementation because diagnostics included `dotenv-size-secret`, `dotenv-link-secret`, or raw `UnicodeDecodeError` text.
- `python3 -m pytest tests/test_servicenow.py -q -k "dotenv_values_oversized_error or dotenv_values_regular_file_error or dotenv_values_invalid_utf8 or oversized_env_without_whole_file_text_read or symlinked_env_file"`: 5 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 193 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 512 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2302 total tests passed at 93.97% coverage.
