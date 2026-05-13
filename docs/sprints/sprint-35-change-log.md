# Sprint 35 Change Log

## Candidate Failure Isolation

- Added failure isolation to `run-implementation-candidates`.
- Recorded per-story blocked outcome entries when candidate generation or artifact writing fails.
- Kept successful jobs writing candidate artifacts while the batch continues processing later jobs.
- Returned a nonzero exit code when one or more jobs are blocked.

## Operator Boundary

- Preserved safe summary output with total, built, and blocked counts.
- Wrote blocked reasons into the candidate batch report without ServiceNow sys_id values.
