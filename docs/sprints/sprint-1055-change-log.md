# Sprint 1055 Change Log

## Backup and Restore Runbook

- Documented that PostgreSQL is the authoritative operational store for JEDI
  lifecycle events, fulfillment jobs, job events, artifact refs, DB-backed
  artifact blobs, retention audit rows, and builder maturity evidence.
- Made the production boundary explicit: retention pruning is not backup, and
  artifact-reference/audit-chain rows must not be deleted as a storage shortcut.
- Added production expectations for encrypted PostgreSQL backups, access logging,
  point-in-time recovery, customer-approved RPO and RTO targets, and restore
  drill evidence.
- Added a restore drill procedure covering restored staging databases,
  `init-operational-store`, `GET /ready`, `GET /admin/operations`, restored
  lifecycle/job/artifact trace inspection, and required operations evidence.

## Verification

- `pytest tests/test_project_docs.py::test_sprint_1055_documents_backup_restore_runbook -q`
- `test_sprint_1055_documents_backup_restore_runbook`
