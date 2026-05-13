# Sprint 27 Change Log

## manifest alignment

- Updated README scope to include Controlled ServiceNow story writeback.
- Replaced the ambiguous blanket live-write exclusion with specific prohibited actions.
- Kept Direct Update Set imports, commits, deployments, and production promotions out of MVP scope.
- Documented `execute_writeback()` and `run_writeback_batch()` as the automated writeback boundaries.

## Controlled Writeback Scope

- Limited writeback to external build evidence and `Ready for Testing`.
- Documented state discovery, dictionary field validation, actor identity, confirmation, idempotency, and audit artifact requirements.
- Clarified that unvalidated ServiceNow mutation remains out of scope.
