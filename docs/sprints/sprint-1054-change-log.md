# Sprint 1054 Change Log

## Admin Operations Summary

- Added a failing-first PostgreSQL store test for `fulfillment_job_status_summary()`.
- Added `FulfillmentJobStatusSummaryRecord` and a DB-backed aggregate query over
  `fulfillment_jobs` so operators can see real backlog, terminal counts, and
  stale-running counts without sampling recent jobs.
- Added authenticated `GET /admin/operations`, protected by the existing admin bearer token and rate limiter, returning `queued`, `running`, `completed`,
  `failed`, `rejected`, `stale_running`, `total`, and the configured stale-job
  threshold.
- Documented the endpoint in `docs/operator-guide.md` as a non-mutating
  operational summary that does not infer state from `/admin/jobs`.

## Verification

- `pytest tests/test_operational_store.py::test_fulfillment_job_status_summary_uses_postgres_aggregate_counts -q`
- `pytest tests/test_runtime.py::test_admin_operations_returns_db_backed_fulfillment_summary -q`
- `test_fulfillment_job_status_summary_uses_postgres_aggregate_counts`
- `test_admin_operations_returns_db_backed_fulfillment_summary`
