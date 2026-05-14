# Sprint 74 Change Log

## Goal

Add a containerized local runtime for the API, worker, and PostgreSQL services.

## Changes

- Added `Dockerfile` for the Python runtime image.
- Added `.dockerignore` to keep local secrets, generated artifacts, caches, and git metadata out of the build context.
- Added `docker-compose.yml` with `api`, `worker`, and `postgres` services.
- Added `jedi_devproject.runtime_api` as the Uvicorn factory entrypoint.
- Added `jedi_devproject.runtime_worker` as the one-shot worker process entrypoint.
- Kept `JEDI_BUILD_CLAIM_APPLY=false` as the local compose default.

## Verification

- Added container-runtime tests for Dockerfile, Compose topology, operator documentation, and sprint evidence.
- Added runtime entrypoint tests for API app construction and worker delegation.

## Architecture Notes

The API container uses Uvicorn factory mode so runtime settings and PostgreSQL connections are created when the host starts the app, not during Python package import. The worker remains a one-shot process so the host can decide whether to run it on a schedule, in a loop, or through a future process supervisor.
