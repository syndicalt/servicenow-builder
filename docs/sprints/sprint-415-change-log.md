# Sprint 415 Change Log

## Runtime-configurable rate-limit bucket caps

Promoted rate-limit bucket cardinality caps into runtime configuration. Sprint 414 bounded the shared limiter internally, but lifecycle and admin API processes still used the hardcoded default, which made the memory-vs-fairness tradeoff impossible to tune per deployment.

The runtime now exposes `JEDI_LIFECYCLE_RATE_LIMIT_MAX_BUCKETS` and `JEDI_ADMIN_RATE_LIMIT_MAX_BUCKETS`. Both settings use the same strict ASCII base-10 integer parser as the existing request/window rate-limit settings, are validated as positive integers during runtime validation, and are passed into the lifecycle and admin `InMemoryRateLimiter` instances created by `create_runtime_api()`.

This lets operators tune high-cardinality ingress behavior separately for lifecycle webhook traffic and admin diagnostic traffic while keeping the default at 10000 live buckets per process.

## Verification

- Added focused tests that failed before implementation because the settings model ignored max-bucket fields and runtime limiter construction did not pass a bucket cap.
- `python3 -m pytest tests/test_runtime.py -q -k "runtime_settings_reads_lifecycle_webhook_configuration or non_positive_runtime_limits or admin_rate_limiter_uses_runtime_bucket_cap or malformed_runtime_integer_values or padded_runtime_integer_values or signed_runtime_integer_values"`: 21 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 191 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 489 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2236 total tests passed at 93.95% coverage.
