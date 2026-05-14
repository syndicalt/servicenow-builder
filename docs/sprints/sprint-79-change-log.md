# Sprint 79 Change Log

## Goal

Start moving from a manually invoked worker to a hosted long-running worker runtime while enabling the live `Ready` to `Work in Progress` build claim in the Railway development environment.

## Changes

- Set Railway `JEDI_BUILD_CLAIM_APPLY=true` so the build-claim stage can move live ServiceNow stories to `Work in Progress`.
- Added worker loop settings for `JEDI_WORKER_MAX_ITERATIONS`, `JEDI_WORKER_IDLE_SLEEP_SECONDS`, and `JEDI_WORKER_STOP_ON_FAILURE`.
- Changed `python -m jedi_devproject.runtime_worker` to run the configured loop rather than a one-shot job.
- Added `Dockerfile.worker` so the hosted worker can run `python -m jedi_devproject.runtime_worker` without changing the API service command.
- Documented the intended Railway worker service name as `jedi-devproject-worker`.

## Verification

- Added worker entrypoint tests for environment-driven loop configuration.
- Added bounded-loop main test coverage so hosted behavior can be exercised without an infinite test process.
- Added container-runtime coverage for `Dockerfile.worker`.

## Architecture Notes

The public API service must remain dedicated to receiving lifecycle webhooks. The worker must run as a separate process or service so lifecycle events enqueue quickly and fulfillment happens outside the webhook request. For Railway, the worker should use the same repository with `RAILWAY_DOCKERFILE_PATH=Dockerfile.worker` and shared runtime variables.
