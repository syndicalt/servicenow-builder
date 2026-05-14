# Sprint 88 Change Log

## Goal

Add tested ServiceNow CI/CD Update Set lifecycle request methods without enabling automated promotion.

## Changes

- Added `retrieve_cicd_update_set()` for `POST /api/sn_cicd/update_set/retrieve`.
- Added `preview_cicd_update_set()` for `POST /api/sn_cicd/update_set/preview/{remote_update_set_id}`.
- Added `commit_cicd_update_set()` for `POST /api/sn_cicd/update_set/commit/{remote_update_set_id}` with `force_commit=false` by default.
- Added `fetch_cicd_progress()` for `GET /api/sn_cicd/progress/{progress_id}`.
- Kept all CI/CD lifecycle operations out of automated story fulfillment.

## Tests

- Added ServiceNow client request-shape coverage for retrieve, preview, commit, and progress.
- Verified retrieve sends update source parameters and boolean flags as explicit query values.
- Verified commit defaults to non-force commit.

## Decision

The CI/CD Update Set API is now available as a typed integration boundary, but promotion is still not automatic. The next architecture decision is where the source update set comes from: a build/source ServiceNow instance or a reviewed ServiceNow-side XML importer.
