# Sprint 446 Change Log

## Alert sink response diagnostic key sanitization

Hardened alert webhook failure diagnostics so response object keys are treated as untrusted sink output. Prior behavior recursively redacted response values but preserved dictionary keys as-is. That allowed secret-like response keys such as `client_secret=...` or URL query strings to appear in `AlertDeliveryError`, and non-string keys supplied by alternate transports could crash diagnostic serialization when `json.dumps(..., sort_keys=True)` compared incompatible key types.

Alert sink response diagnostics now sanitize dictionary keys before serialization:

- secret-like key text is redacted with the shared diagnostic redactor
- whitespace and control characters are collapsed
- oversized keys are capped
- non-string keys become `[non-string key]`
- duplicate sanitized labels receive deterministic duplicate suffixes instead of overwriting values

The value redaction, traversal bounds, whole-response cap, and non-JSON value handling remain intact.

## Verification

- Added 2 failing-first alert delivery tests covering secret-like response keys and non-string response keys.
- `python3 -m pytest tests/test_alert_delivery.py -q -k "sensitive_response_keys or non_string_response_keys"`: failed before implementation because key text leaked and non-string keys crashed JSON serialization.
- `python3 -m pytest tests/test_alert_delivery.py -q -k "sensitive_response_keys or non_string_response_keys or alert_response_diagnostic_does_not_consume_all_fields"`: 3 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 194 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 520 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2330 total tests passed at 93.93% coverage.
