# Sprint 358 Change Log

## Persisted admin diagnostic response bounds

Hardened admin diagnostic rendering so persisted failure text cannot create oversized API or HTML
responses after it has already been stored. Previous controls redacted secrets from runtime
diagnostic surfaces, but long persisted strings such as provider output fragments, worker failure
messages, artifact reference paths, or artifact payload diagnostic values could still be returned at
full length through `/admin/jobs`, `/jobs/{job_id}/events`, `/jobs/{job_id}/artifacts`,
`/artifacts/{artifact_id}`, `/admin/alerts`, or the HTML admin console.

Admin diagnostic strings now pass through one shared post-redaction size cap. The helper first
applies the existing credential, URL, header, cookie, private-key, and sensitive-query redaction
rules, then truncates oversized diagnostic strings with `...[truncated]`. The control is used for
fulfillment job `last_error` values, job event messages, artifact reference paths, operational alert
details, and recursive string values inside artifact payload diagnostic views. Normal short
diagnostics keep their existing shape, and artifact SHA-256 values remain the durable provenance
check for the original unredacted stored payload.

## Tests

- Failing-first coverage: 3 tests failed before implementation, proving persisted admin job errors, job event messages, and artifact payload diagnostic strings were redacted but still returned at full size.
- Focused verification: `python3 -m pytest tests/test_runtime.py -q -k "bounds_persisted or bound_persisted"` passed after implementation.
- Admin diagnostic regression verification: `python3 -m pytest tests/test_runtime.py -q -k "admin_jobs_redacts or admin_alerts_lists or admin_console_redacts or job_events_returns_correlation or artifact_read_redacts or bounds_persisted or bound_persisted"` passed with 9 tests.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 187 source files, 432 documentation tests passed, and 2043 total tests passed at 94.07% coverage.
