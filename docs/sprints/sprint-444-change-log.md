# Sprint 444 Change Log

## Anthropic max-token ASCII integer parsing

Hardened `ANTHROPIC_MAX_TOKENS` environment parsing so provider configuration cannot silently normalize numeric-looking deployment input. Prior behavior used Python `int(text)`, which accepted signed values such as `+8192`, underscore-separated values such as `8_192`, and non-ASCII digit strings such as `８１９２`.

`ANTHROPIC_MAX_TOKENS` now reuses the shared strict numeric parser and must be ASCII base-10 digits only before Anthropic-specific positive and maximum-token bounds run. Malformed values fail with a stable diagnostic naming `ANTHROPIC_MAX_TOKENS` and the ASCII base-10 requirement without echoing the submitted value.

## Verification

- Added 3 failing-first Anthropic provider config tests covering signed, underscore-separated, and non-ASCII digit max-token values.
- `python3 -m pytest tests/test_anthropic_provider.py -q -k "normalized_numeric_max_tokens"`: failed before implementation because all three malformed numeric forms were accepted.
- `python3 -m pytest tests/test_anthropic_provider.py -q -k "max_tokens or whitespace or reads_all_values or applies_defaults"`: 15 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 194 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 518 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2322 total tests passed at 93.97% coverage.
