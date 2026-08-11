# Sprint 406 Change Log

## Bounded lifecycle webhook credentials

Hardened lifecycle webhook authentication so oversized inbound credential headers are rejected before parsing or comparison. The prior lifecycle ingress checks rejected padded, whitespace-bearing, and control-character-bearing credentials, but did not cap header length at the application boundary.

Lifecycle webhook timestamp, HMAC signature, and interim shared-secret header values are now capped at 8 KiB. Oversized timestamps are rejected before integer parsing or replay-window clock checks, and oversized signatures or shared secrets are rejected before constant-time comparison. This keeps malformed ServiceNow emitters, proxy rewriting mistakes, and credential-probe traffic from turning lifecycle auth into unnecessary CPU work.

## Tests

- Failing-first coverage: 3 tests failed before implementation, proving oversized lifecycle webhook timestamp, HMAC signature, and shared-secret values reached parsing or constant-time comparison.
- Focused verification: `python3 -m pytest tests/test_lifecycle_api.py -q -k "oversized_timestamp_before_int_parse or oversized_signature_before_compare or oversized_secret_before_compare"` passed with 3 tests.
- Broader lifecycle verification: `python3 -m pytest tests/test_lifecycle_api.py -q` passed with 31 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 190 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 190 source files, 480 documentation tests passed, and 2195 total tests passed at 93.93% coverage.
