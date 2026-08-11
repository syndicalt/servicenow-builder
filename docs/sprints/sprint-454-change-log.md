# Sprint 454 Change Log

## Alert sink response depth-bound diagnostic hardening

Hardened alert sink response diagnostics so deeply nested but acyclic response payloads cannot force unbounded recursive redaction work before an `AlertDeliveryError` is formatted. Prior behavior bounded collection width and handled cycles, but it still traversed arbitrary nesting depth and could reach irrelevant leaf values in malformed sink responses.

Alert response redaction now caps nested dictionary, list, and tuple projection at a fixed diagnostic depth. Containers beyond the cap render as `[max depth exceeded]`, while existing cycle handling, sensitive-key redaction, non-string key handling, non-JSON value markers, width bounds, and whole-diagnostic caps remain intact.

## Verification

- Added 1 failing-first alert response diagnostic test covering an excessively deep acyclic sink response payload.
- `python3 -m pytest tests/test_alert_delivery.py -q -k "excessive_response_depth"`: failed before implementation because the diagnostic reached the leaf sink failure message.
- `python3 -m pytest tests/test_alert_delivery.py -q -k "excessive_response_depth or circular_response_payloads or sensitive_response_keys or non_string_response_keys or non_json_response_values or alert_response_diagnostic_does_not_consume_all_fields"`: 6 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 195 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 528 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2347 total tests passed at 93.79% coverage.
