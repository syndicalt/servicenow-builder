# Sprint 445 Change Log

## Anthropic retry-after ASCII decimal parsing

Hardened Anthropic provider `retry-after` response-header parsing so upstream rate-limit headers cannot silently normalize numeric-looking values into worker sleep durations. Prior behavior used Python `float(retry_after_header)`, which accepted signed values such as `+7`, underscore-separated values such as `7_0`, exponent notation such as `1e2`, and non-ASCII digit strings such as `７`.

Anthropic retry handling now reuses the shared strict ASCII decimal parser. Safe decimal second values such as `7` and `7.5` remain supported and are still capped at the 30-second provider backoff maximum. Malformed `retry-after` values are ignored and fall back to deterministic exponential backoff without echoing the upstream header value.

## Verification

- Added 4 failing-first Anthropic provider retry tests covering signed, underscore-separated, exponent-notation, and non-ASCII digit `retry-after` values.
- `python3 -m pytest tests/test_anthropic_provider.py -q -k "ignores_malformed_retry_after_header"`: failed before implementation because those four malformed values changed worker sleep behavior.
- `python3 -m pytest tests/test_anthropic_provider.py -q -k "retry_after"`: 10 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 194 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 519 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2327 total tests passed at 93.96% coverage.
