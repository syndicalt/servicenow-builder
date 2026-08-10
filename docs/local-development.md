# Local Development

Run and verify the JEDI DevProject sidecar locally: the lint, type, and test gate, read-only
live smoke checks, implementation packet and candidate review, and lifecycle smoke runs.
Install and configure the runtime first with `docs/installation.md`. For test strategy and
test-writing rules, see `docs/development.md`. For the full lifecycle and writeback contracts
behind these smoke runs, see `docs/runtime-operations.md`.

## Contents

- [Verification](#verification) — the full local gate and the CI verification workflow contract.
- [Live Smoke Testing](#live-smoke-testing) — manual, read-only ServiceNow smoke checks and transport boundaries.
- [Implementation Packet Review](#implementation-packet-review) — packet, candidate, and batch candidate CLI workflows.
- [Lifecycle Smoke](#lifecycle-smoke) — the dry-run lifecycle runner from story fetch through writeback planning.
- [Container Lifecycle Smoke](#container-lifecycle-smoke) — the compose-based end-to-end smoke sequence.

## Verification

Run the full local gate:

```bash
python3 -m ruff check src tests && python3 -m bandit -q -r src && python3 -m pip_audit . --progress-spinner off && python3 -m mypy src tests && python3 -m pytest --cov=jedi_devproject --cov-report=term-missing --cov-fail-under=90
```

CI verification gate. Pull requests and pushes to `master` run `.github/workflows/ci.yml`, which installs the package with development dependencies and executes `python3 -m ruff check src tests`, `python3 -m bandit -q -r src`, `python3 -m pip_audit . --progress-spinner off`, `python3 -m mypy src tests`, and `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`. Workflow command steps use `bash` with `set -euo pipefail` so failures stop the job instead of continuing with partial verification.

CI workflow token permissions are read-only. `.github/workflows/ci.yml` declares
`permissions: contents: read` because verification needs repository checkout but does not need
`contents: write`, `pull-requests: write`, package publishing, deployment, or issue mutation scope.

CI verification cancels stale runs. `.github/workflows/ci.yml` uses a top-level concurrency group
keyed by `github.workflow` and `github.ref` with `cancel-in-progress: true`, so superseded pushes or
PR updates do not leave older verification results competing with the current commit.

CI checkout does not persist credentials. The verification workflow uses the `actions/checkout`
step with `persist-credentials: false`, so the read-only `GITHUB_TOKEN` used for checkout is not
left in the job's git configuration for later lint, typecheck, or test steps.

CI third-party actions are pinned to commit SHAs. The workflow uses immutable commit refs for
`actions/checkout` and `actions/setup-python`, not mutable major-version tags. Update these SHAs
intentionally during dependency maintenance after reviewing the upstream action releases.

Runtime Dockerfiles pin the Python base image digest. `Dockerfile` and `Dockerfile.worker` use
`python:3.13-slim@sha256:9662417aace5ae7b8e2609cce472b72a8958e134ba372808abe9cc1a0c0125e6`
instead of the mutable `python:3.13-slim` tag alone. Refresh this digest deliberately during base
image maintenance after reviewing the upstream Python image release and rebuilding both API and
worker images.

Runtime Dockerfiles do not upgrade pip during image builds. The API and worker images run
`pip install --no-cache-dir .` with the pip version supplied by the pinned Python base image instead
of `--upgrade pip`, avoiding an extra mutable build-time package-manager fetch after the base image
digest has been selected.

Runtime Dockerfiles define pip build environment defaults. API and worker images set
`PIP_DISABLE_PIP_VERSION_CHECK=1`, `PIP_NO_CACHE_DIR=1`, and `PIP_ROOT_USER_ACTION=ignore` before the
package install step. This keeps image builds from performing pip version-check calls, writing pip
caches into layers, or emitting root-user warnings from the intentional build-time install phase.

Compose pins the PostgreSQL image digest. The local operational-store service uses
`postgres:16@sha256:95206741a5b214807675e14165369d05b93a9cf692223b616d07cca227e74b0b`
instead of the mutable `postgres:16` tag alone. Refresh this digest deliberately during database
base image maintenance after reviewing the upstream Postgres image release and validating local
compose startup.

Compose reduces PostgreSQL container privileges without read-only root. The local Postgres service
uses `no-new-privileges:true` and `pids_limit: 512` to reduce privilege-escalation and process-fork
risk, while keeping the normal writable data volume and official-image startup behavior intact.

Compose gives PostgreSQL an explicit graceful shutdown window. The local Postgres service uses
`stop_signal: SIGTERM` with `stop_grace_period: 60s`, giving the operational-store container a
database-specific stop window instead of relying on the Docker engine default or the shorter app
service shutdown window.

## Live Smoke Testing

Live smoke tests should be manual and read-only. They should request an OAuth token and query `rm_story` with `sysparm_limit=1`.

ServiceNow OAuth token responses must be exact `HttpResponse` objects before the client reads
status or body fields. OAuth status codes must be exact integers in the `100..599` range; malformed
transport objects, status-code objects, and out-of-range values fail with fixed diagnostics before
attribute comparison hooks, stringification, or token parsing can leak credential material.
ServiceNow OAuth response bodies must be exact dictionaries before access-token lookup. Mapping-like
objects and dict subclasses cannot override token lookup or execute custom `get()` hooks; they fail
with a fixed OAuth body diagnostic before token validation.
Successful ServiceNow API response bodies must be exact dictionaries before the shared response-body
helper copies them or appends transport metadata. The shared response-body helper rejects malformed
bodies with a fixed diagnostic. In this boundary, shared response-body helper rejects mapping objects and dict subclasses before corrupted transport output can execute iteration hooks or subclass methods during CICD progress, update-set import, or update-set action handoff handling.
Successful ServiceNow API responses must be exact `HttpResponse` objects before the shared helper
branches on success or failure. ServiceNow API status codes must be exact integers in the `100..599` range; malformed response objects, status-code objects, and out-of-range values fail with fixed diagnostics before comparison hooks, diagnostic formatting, or body handling can leak credential material.
ServiceNow API error diagnostic bodies must be exact dictionaries before rich diagnostic shaping.
Arbitrary non-dictionary error bodies and top-level dict subclasses collapse to `[non-json value]`
instead of entering key iteration, length checks, redaction, or `repr()` formatting. Exact dictionary
error bodies keep the existing bounded redaction, key projection, duplicate-key handling, and final
diagnostic truncation behavior.
ServiceNow Table API result bodies must be exact dictionaries before `result` extraction. The shared
result extraction rejects mapping objects and dict subclasses before reading `result`, so malformed
transport output cannot override lookup behavior or execute custom `get()` hooks while stories,
choices, dictionary fields, updates, attachments, or retrieved update-set records are parsed.
ServiceNow Table API responses must pass the shared exact response/status boundary before success,
failure, or result parsing. In this path, regular Table API methods no longer branch directly on `response.status_code`; malformed response objects, status-code objects, and out-of-range status values fail with the same fixed ServiceNow API response diagnostics used by CICD handoff helpers.
ServiceNow CICD probe responses are observational but still boundary-checked before operator output.
The probe validates exact `HttpResponse` transport output, exact HTTP-range integer status codes, and
exact dictionary response bodies before copying body fields and appending `status_code`. In this
observational path, valid HTTP error statuses remain returned as probe data, so unsupported endpoint
behavior can still be reported without changing instance state.
ServiceNow API error formatting requires a prevalidated integer status code from the shared
response/status boundary. In this path, the formatter no longer falls back to `response.status_code`, so internal
call-site regressions cannot execute hostile status object stringification while building API error
diagnostics.

Do not print tokens, secrets, sys_ids, or sensitive story content in user-facing summaries.

## Implementation Packet Review

Use `build-implementation-packet` to produce a reviewable implementation packet artifact before any model integration is called:

```bash
python3 -m jedi_devproject.cli build-implementation-packet \
  --sample-file artifacts/stories/STRY0010013.json \
  --artifact-root artifacts/implementation-packets \
  --run-id packet-run-20260513-001
```

For a read-only PDI story fetch, use the story number instead of a local file:

```bash
python3 -m jedi_devproject.cli build-implementation-packet \
  --env-file .env \
  --story-number STRY0010013 \
  --artifact-root artifacts/implementation-packets \
  --run-id packet-run-20260513-001
```

The command runs deterministic safety, risk, provider-policy, and specialized RAG context gates, then writes one packet JSON file per story. The packet is shaped for the Now Assist implementation path, but this command does not call a model.

Packet artifacts exclude the ServiceNow story `sys_id`. They include the story number, minimized story text, allowed tables, allowed operations, citations, compliance context, risk score, and the required model output contract.

Use `build-implementation-candidate` to validate an explicit provider response and write a validated implementation candidate artifact:

```bash
python3 -m jedi_devproject.cli build-implementation-candidate \
  --sample-file artifacts/stories/STRY0010013.json \
  --provider-response-file artifacts/provider-responses/STRY0010013.json \
  --artifact-root artifacts/implementation-candidates \
  --run-id candidate-run-20260513-001
```

The same command can use a read-only PDI story source:

```bash
python3 -m jedi_devproject.cli build-implementation-candidate \
  --env-file .env \
  --story-number STRY0010013 \
  --provider-response-file artifacts/provider-responses/STRY0010013.json \
  --artifact-root artifacts/implementation-candidates \
  --run-id candidate-run-20260513-001
```

The provider response file must be a JSON object containing allowed changes plus `test_plan` and `rollback_notes`. The command validates the response against the deterministic implementation packet gates, then writes a write-once `UpdateSetCandidate` artifact. Unsafe provider responses fail before any artifact is written.

This command is a dry-run operator adapter for a future approved model provider. It does not call Now Assist or any external model endpoint.

For file-based batch orchestration, provide an implementation candidate jobs file:

```json
[
  {
    "sample_file": "artifacts/stories/STRY0010013.json",
    "provider_response_file": "artifacts/provider-responses/STRY0010013.json"
  }
]
```

Run it with:

```bash
python3 -m jedi_devproject.cli run-implementation-candidates \
  --jobs-file artifacts/implementation-candidate-jobs.json \
  --artifact-root artifacts/implementation-candidates \
  --batch-report-root artifacts/implementation-candidate-batches \
  --run-id candidate-batch-20260513-001
```

Empty job files fail closed with `reason=no_jobs`. The command prints a safe summary with total, built, and blocked counts. Successful runs also write a write-once batch report containing the summary and per-story outcomes. Reports do not include ServiceNow sys_ids.

## Lifecycle Smoke

Use `run-lifecycle-smoke` to exercise the current dry-run lifecycle from PDI story fetch through writeback planning:

```bash
python3 -m jedi_devproject.cli run-lifecycle-smoke \
  --env-file .env \
  --story-number STRY0010013 \
  --provider-response-file artifacts/provider-responses/STRY0010013.json \
  --artifact-root artifacts/lifecycle-smoke \
  --run-id lifecycle-smoke-20260513-001 \
  --build-reference build-lifecycle-smoke-20260513-001 \
  --from-state Ready
```

The smoke runner writes an implementation packet, validated candidate artifact, candidate batch report, and writeback plan summary. It does not mutate ServiceNow. Missing stories fail closed before artifact creation.

The smoke runner also writes a lifecycle manifest under `artifacts/lifecycle-smoke/lifecycle-manifests/<run-id>.json`. The manifest is a single audit index for the run and includes SHA-256 hashes for the implementation packet, implementation candidate, candidate batch report, and writeback outcome. It does not include ServiceNow sys_ids.

## Container Lifecycle Smoke

Use `plan_container_lifecycle_smoke()` in `jedi_devproject.container_smoke` to produce the safe smoke sequence for the local runtime. The smoke plan keeps apply disabled and uses a synthetic `Draft` to `Ready` lifecycle event for the selected story number.

The manual sequence is:

```bash
docker compose up -d postgres api
```

Post the planned event payload to:

```text
POST http://localhost:8000/lifecycle/events
```

Then run one worker pass:

```bash
docker compose run --rm worker
```

The smoke should enqueue and claim the job, then dry-run the build claim through the existing guarded writeback path. It must not mutate ServiceNow while `JEDI_BUILD_CLAIM_APPLY=false`.

If the worker reports `fresh_story_state_mismatch`, treat that as a safety pass for stale synthetic input rather than a runtime failure. It means the live ServiceNow story no longer matches the `Draft` to `Ready` event used to enqueue the job. A full fulfillment smoke should be driven by the actual ServiceNow transition that creates the lifecycle event.
