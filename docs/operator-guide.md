# Operator Guide

## Local Configuration

Create a local `.env` file using `.env.example` as the template:

```bash
SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com
SERVICENOW_CLIENT_ID=...
SERVICENOW_CLIENT_SECRET=...
```

Never commit `.env`.

## Verification

Run the full local gate:

```bash
python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest --cov=jedi_devproject --cov-report=term-missing --cov-fail-under=90
```

## Live Smoke Testing

Live smoke tests should be manual and read-only. They should request an OAuth token and query `rm_story` with `sysparm_limit=1`.

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

## Operational Store

The runtime uses PostgreSQL for durable operational state and keeps large, reviewable filesystem artifacts as files under the controlled workspace. PostgreSQL is the MVP store for lifecycle orchestration because the API and worker runtime need production-shaped transactions, foreign keys, JSONB event payloads, and row-level worker claims from the start.

The operational schema is defined in `db/migrations/0001_operational_store.sql` and initialized by `connect_operational_store(database_url=...)` in `jedi_devproject.operational_store`. It includes:

- `lifecycle_events`: inbound ServiceNow lifecycle events and their preserved original payload.
- `fulfillment_jobs`: one idempotent fulfillment job per lifecycle event, including status, attempt count, and worker lock metadata.
- `job_events`: append-only status history for queued, running, completed, blocked, or failed job transitions.
- `artifact_refs`: references to generated filesystem artifacts with SHA-256 hashes.

The current claim primitive is `claim_next_fulfillment_job(worker_id=...)`. It uses `SELECT ... FOR UPDATE SKIP LOCKED` inside a PostgreSQL transaction to select the oldest queued job, mark it `running`, increment the attempt count, and set `locked_by` and `locked_at`. API and worker processes should use this store instead of treating JSON files as a queue.

## Lifecycle Webhook API

The local runtime exposes a FastAPI application from `create_lifecycle_api()` in `jedi_devproject.lifecycle_api`. Production wiring must provide `DATABASE_URL` for `connect_operational_store(database_url=...)`, then inject that store into the API factory.

The lifecycle receiver is:

```text
POST /lifecycle/events
```

A valid `Draft` to `Ready` `LifecycleStateChangeEvent` returns `202 Accepted`, records the event in `lifecycle_events`, enqueues one `fulfillment_jobs` row, and returns the queued `job_id`. Unsupported lifecycle transitions are still accepted and recorded, but they are not enqueued for fulfillment.

The webhook request path does not execute fulfillment inline. Build evaluation, ServiceNow claim writeback, implementation packet generation, external build handoff, and Ready for Testing writeback must run in worker processing after a queued job is claimed.

## Fulfillment Worker

The worker boundary is `process_one_fulfillment_job()` in `jedi_devproject.fulfillment_worker`. It claims one queued job from PostgreSQL with `claim_next_fulfillment_job(worker_id=...)`, calls an injected fulfillment handler, and records the terminal job state.

Successful handlers call `complete_fulfillment_job()` and append a `completed` job event. Handler failures call `fail_fulfillment_job()`, store the error in `last_error`, clear the worker lock, and append a `failed` job event.

The first production handler is `build_claim_fulfillment_handler()` in `jedi_devproject.fulfillment_handler`. It converts a claimed fulfillment job into an `execute_build_claim()` request, using the job story number and lifecycle event id to move the story from `Ready` to `Work in Progress` through the existing guarded writeback path.

The worker runs outside the webhook request. The webhook should only validate, record, enqueue, and acknowledge lifecycle events.

## Runtime Wiring

Runtime configuration is loaded by `load_runtime_settings()` in `jedi_devproject.runtime`. Required environment values are:

- `DATABASE_URL`
- `SERVICENOW_INSTANCE_URL`
- `SERVICENOW_CLIENT_ID`
- `SERVICENOW_CLIENT_SECRET`
- `JEDI_AUDIT_ROOT`

Optional values are `JEDI_WORKER_ID` and `JEDI_BUILD_CLAIM_APPLY`. The API process should call `create_runtime_api()` with these settings. The worker process should call `process_one_runtime_fulfillment()` in a loop or scheduler owned by the runtime host.

## Container Runtime

The local container runtime is defined by `Dockerfile` and `docker-compose.yml`. It starts three services:

- `postgres`: PostgreSQL operational state.
- `api`: FastAPI lifecycle receiver.
- `worker`: one-shot fulfillment worker process.

Run the local stack with:

```bash
docker compose up --build
```

The compose file expects ServiceNow OAuth values in the host environment: `SERVICENOW_INSTANCE_URL`, `SERVICENOW_CLIENT_ID`, and `SERVICENOW_CLIENT_SECRET`. It sets `DATABASE_URL` to the local `postgres` service and writes audit output under `/app/artifacts/audit`.

`JEDI_BUILD_CLAIM_APPLY` defaults to `false` in compose. Keep it false for local runtime verification until the story, webhook, and writeback behavior have been reviewed for the target PDI.

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

## Lifecycle Event Contract

ServiceNow should remain the human work surface. For automated orchestration, ServiceNow should emit explicit lifecycle events to the sidecar rather than using comments or work notes as machine commands.

The first inbound event contract is `LifecycleStateChangeEvent` in `jedi_devproject.lifecycle_events`. It represents an `rm_story` state change emitted by a ServiceNow Business Rule or equivalent ServiceNow automation into a sidecar Scripted REST API endpoint.

Required fields:

- `event_id`
- `event_type`
- `source`
- `table`
- `story_number`
- `previous_state`
- `current_state`
- `occurred_at`
- `correlation_id`
- `emitted_by`

For the MVP, only `event_type=story_state_changed`, `table=rm_story`, `previous_state=Draft`, and `current_state=Ready` plans evaluation. The sidecar plan is `evaluate_story` with a later claim target of `Work in Progress`. That claim must still perform a fresh ServiceNow story read and allowlisted state-transition check before any mutation.

The event boundary rejects unknown fields, including ServiceNow `story_sys_id`. Story number, idempotency key, correlation id, source, and emitted identity are enough for orchestration correlation without passing internal ServiceNow record identifiers through the external boundary.

Bootstrap should eventually install or document the ServiceNow-side pieces needed for this contract: a Business Rule or Flow that detects `Draft` to `Ready`, a Scripted REST API or outbound REST Message path for event delivery, and the integration identity used in `emitted_by`. That bootstrap work must be explicit and reviewed; this contract alone does not create ServiceNow scripts.

Business Rule first is the preferred lifecycle trigger bootstrap. A scoped after-update Business Rule on `rm_story` is deterministic, can inspect `previous` and `current` state, and is easier to review in an Update Set than a Flow. Flow remains a later option for approval composition, but the state-change emitter should stay small and table-local.

Use `plan-lifecycle-business-rule` to write a reviewable ServiceNow script artifact:

```bash
python3 -m jedi_devproject.cli plan-lifecycle-business-rule \
  --endpoint-url https://sidecar.example.gov/lifecycle/events \
  --integration-identity jedi-devproject-lifecycle-integration \
  --draft-state-value -6 \
  --ready-state-value 1 \
  --run-id lifecycle-business-rule-20260513-001 \
  --spec-root artifacts/lifecycle-bootstrap
```

The command writes a local lifecycle webhook bootstrap bundle with two reviewed sections:

- `rest_message`: an Outbound REST Message named `Jedi DevProject Lifecycle Event API` with method `post_event`, HTTPS endpoint, JSON content type, and authentication marked `configured_in_servicenow`.
- `business_rule`: the `rm_story` after-update Business Rule script and condition.

The Business Rule references the named REST Message instead of setting the endpoint directly. This keeps the endpoint URL out of the Business Rule script, lets ServiceNow own authentication configuration, and gives reviewers a clean separation between trigger logic and transport configuration.

The generated Business Rule emits `story_state_changed` only when the state changes from the supplied Draft value to the supplied Ready value. The generated payload uses story number and correlation ids, not `story_sys_id`. This command does not install the Business Rule, create a Flow, or mutate ServiceNow.

The artifact also includes `servicenow_records`, a deterministic plan for the ServiceNow tables that later apply code must create or update:

- `sys_rest_message`
- `sys_rest_message_fn`
- `sys_script`

Each record includes an `insert_or_update` operation, lookup keys, and the fields to write. The planning command does not apply those records. Live apply must use this record plan, require explicit confirmation, and write audit evidence before making ServiceNow changes.

The bootstrap writes the public endpoint to ServiceNow's `rest_endpoint` fields and resolves the REST method's `rest_message` parent by the installed REST Message `sys_id`. Verification normalizes ServiceNow boolean strings and reference field `{value, link}` responses before comparing the installed records with the reviewed spec. The current PDI bootstrap uses `no_authentication` because inbound webhook authentication is not implemented yet; authenticated webhook protection is required before any non-PDI use.

Use `apply-lifecycle-webhook` only after reviewing the generated lifecycle bootstrap artifact:

```bash
python3 -m jedi_devproject.cli apply-lifecycle-webhook \
  --env-file .env \
  --spec-file artifacts/lifecycle-bootstrap/lifecycle-business-rule-20260513-001.json \
  --confirm-table rm_story \
  --confirm-records \
  --audit-root artifacts/bootstrap-audit \
  --run-id lifecycle-webhook-apply-20260513-001
```

The command upserts the planned `insert_or_update` records and writes a lifecycle webhook audit artifact. It refuses to call ServiceNow unless `--confirm-table rm_story` and `--confirm-records` are both supplied.

Use `verify-lifecycle-webhook` after apply to perform a read-only comparison between ServiceNow and the reviewed spec:

```bash
python3 -m jedi_devproject.cli verify-lifecycle-webhook \
  --env-file .env \
  --spec-file artifacts/lifecycle-bootstrap/lifecycle-business-rule-20260513-001.json \
  --report-root artifacts/lifecycle-webhook-verification \
  --run-id lifecycle-webhook-verify-20260513-001
```

The command writes a verification report and returns nonzero when expected records are absent or changed. Missing records report `record_missing`; changed fields report `field_mismatch`.

Use `process-lifecycle-event` to validate a captured lifecycle event and write a local orchestration plan:

```bash
python3 -m jedi_devproject.cli process-lifecycle-event \
  --event-file artifacts/lifecycle-events/STRY0010013-ready.json \
  --run-id lifecycle-event-20260513-001 \
  --plan-root artifacts/lifecycle-event-plans
```

The command writes a write-once plan artifact under `lifecycle-event-plans`. A valid `Draft` to `Ready` event plans evaluation and records `Work in Progress` as the later claim state. Invalid events fail closed with `reason=invalid_lifecycle_event` and do not write a plan artifact. This command does not call ServiceNow and does not mutate story state.

## Build Claim Writeback

When a story is eligible for automated fulfillment, the sidecar should claim it before build handoff so users can see that work has started. The application boundary for this is `plan_story_build_claim_writeback()` in `jedi_devproject.writeback`.

The planner allows `Ready` to `Work in Progress` only when state transitions are enabled and that transition is allowlisted by policy. The planned structured fields are:

- `state=Work in Progress`
- `u_ai_status=Build In Progress`
- `u_ai_candidate_artifact=<candidate artifact path>` when available

The work note includes the lifecycle event id used as the orchestration trigger. If state transitions are disabled or the current story state is not allowlisted for `Work in Progress`, the planner fails closed and omits `state` from the planned fields.

This is not live apply. The apply path must still fetch the story fresh from ServiceNow, verify the current state, require an integration actor identity, write audit evidence, and use the same allowlisted field and state-transition controls as the Ready for Testing writeback.

The application boundary for applying this claim is `execute_build_claim()` with `BuildClaimExecutionRequest` in `jedi_devproject.writeback_orchestration`. It performs a fresh story read before mutation and blocks with `fresh_story_state_mismatch` if the story is no longer in the expected source state.

Apply requires:

- `apply=True`
- matching `confirm_story_number`
- service or human `actor_id`
- `audit_root`

Successful apply updates the story to `Work in Progress`, sets `u_ai_status=Build In Progress`, writes the work note, and records a build claim audit artifact. Retries are idempotent when the build claim audit already exists and return `build_claim_already_recorded` without another ServiceNow update.

## Writeback Planning

Before enabling automated writeback, verify the target instance supports the required workflow state and structured fields:

```bash
python3 -m jedi_devproject.cli check-writeback-capability --env-file .env
```

The command is read-only. It checks for the instance `Ready for Testing` state value and required structured writeback fields.

Use `plan-bootstrap-fields` to inspect the missing custom fields required for writeback:

```bash
python3 -m jedi_devproject.cli plan-bootstrap-fields --env-file .env
```

The bootstrap plan only covers custom fields on `rm_story`:

- `u_ai_status`
- `u_ai_build_reference`
- `u_ai_candidate_artifact`

It does not create `state`, and it does not plan form layout changes. Project teams can decide later whether these operational fields should be visible on the Story form.

Use `apply-bootstrap-fields` to create the missing custom table fields after reviewing the plan:

```bash
python3 -m jedi_devproject.cli apply-bootstrap-fields \
  --env-file .env \
  --confirm-table rm_story \
  --confirm-fields \
  --audit-root artifacts/bootstrap-audit \
  --run-id bootstrap-fields-20260513-001
```

The apply command requires both `--confirm-table rm_story` and `--confirm-fields`. It creates only the missing custom fields and writes a bootstrap audit artifact. It makes no form layout changes and does not create `state`.

Use `plan-writeback` to dry-run the ServiceNow writeback that would follow a successful external build:

```bash
python3 -m jedi_devproject.cli plan-writeback \
  --env-file .env \
  --story-number STRY0010013 \
  --build-reference build-20260513-001 \
  --artifact-url artifacts/STRY0010013.json \
  --from-state Ready
```

The command discovers the instance `Ready for Testing` state value from `sys_choice`, plans the field updates, and prints a safe summary. It does not apply ServiceNow updates.

The command also verifies required structured writeback fields on `rm_story` through `sys_dictionary`:

- `state`
- `u_ai_status`
- `u_ai_build_reference`
- `u_ai_candidate_artifact`

If any required field is missing, the command fails closed and does not apply any update.

To apply the validated writeback, the operator must pass both `--apply` and a matching `--confirm-story-number` value:

```bash
python3 -m jedi_devproject.cli plan-writeback \
  --env-file .env \
  --story-number STRY0010013 \
  --build-reference build-20260513-001 \
  --artifact-url artifacts/STRY0010013.json \
  --from-state Ready \
  --apply \
  --confirm-story-number STRY0010013 \
  --actor-type service \
  --actor-id svc-jedi-orchestrator \
  --execution-id run-20260513-001 \
  --audit-root artifacts/writeback-audit \
  --manifest-root artifacts/lifecycle-manifests \
  --packet-path artifacts/lifecycle-smoke/implementation-packets/lifecycle-20260513-001/STRY0010013.json \
  --candidate-path artifacts/lifecycle-smoke/implementation-candidates/lifecycle-20260513-001/STRY0010013.json
```

The dry-run default is intentional. A mismatch between the fetched story number and `--confirm-story-number` blocks the update.

Apply also requires `--actor-id` and `--audit-root`. Automated orchestration should use `--actor-type service` and set `--actor-id` to the service principal, workload identity, or named integration identity that performed the writeback. Manual runs may use `--actor-type human`.

The command writes a local writeback audit artifact before reporting success. Audit artifacts are write-once and include story number, build reference, actor type, actor id, optional execution id, allowed/applied flags, planned fields, and validation reasons. They do not include the ServiceNow story sys_id.

When `--manifest-root`, `--packet-path`, and `--candidate-path` are provided with `plan-writeback --apply`, the command verifies the remote writeback with `verify_writeback()` and writes a lifecycle manifest for the applied run. `--candidate-batch-path` can also be supplied when a candidate batch report exists.

Automated orchestration should call the application boundary directly through `execute_writeback()` in `jedi_devproject.writeback_orchestration`. The CLI is an operator adapter over that same path, not the product integration surface.

Writeback apply is idempotent by writeback audit artifact and remote writeback state. If an identical story/build audit artifact already exists, `execute_writeback()` treats the retry as already recorded and returns a no-op result without issuing another ServiceNow update. If the audit artifact is missing but the ServiceNow story already has the target state and matching `u_ai_build_reference`, orchestration also returns a no-op result instead of appending duplicate work notes.

Use `verify-writeback` after apply to read the remote story and confirm the structured writeback fields match the expected build result:

```bash
python3 -m jedi_devproject.cli verify-writeback \
  --env-file .env \
  --story-number STRY0010013 \
  --build-reference build-20260513-001 \
  --artifact-url artifacts/STRY0010013.json
```

The command is read-only. It discovers the instance `Ready for Testing` state value, fetches the story, and compares `state`, `u_ai_status`, `u_ai_build_reference`, and `u_ai_candidate_artifact`. It prints `verified=True` only when all expected fields match.

For a controlled apply run, use `record-lifecycle-manifest` to tie together artifacts that were produced by separate commands:

```bash
python3 -m jedi_devproject.cli record-lifecycle-manifest \
  --run-id lifecycle-20260513-001 \
  --story-number STRY0010013 \
  --build-reference build-20260513-001 \
  --packet-path artifacts/lifecycle-smoke/implementation-packets/lifecycle-20260513-001/STRY0010013.json \
  --candidate-path artifacts/lifecycle-smoke/implementation-candidates/lifecycle-20260513-001/STRY0010013.json \
  --writeback-audit-path artifacts/writeback-audit/STRY0010013-build-20260513-001.json \
  --verification-verified \
  --verification-state -7 \
  --manifest-root artifacts/lifecycle-manifests
```

Lifecycle manifest files are write-once. They are intended for audit review and should reference artifacts by path and hash, not by ServiceNow sys_id.

## External Build Pipeline Contract

The external builder boundary is represented by `ExternalBuildPipelineResult` in `jedi_devproject.external_build`. This is a typed artifact contract, not a build executor.

Required fields:

- `story_number`
- `build_reference`
- `status`
- `candidate_artifact_path`
- `build_actor_id`

Successful builds also require:

- `reviewed_update_set_xml_path`
- `test_evidence_path`

The contract rejects unknown fields, including ServiceNow `story_sys_id`. The sidecar should use story number and artifact references at this boundary.

Use `writeback_job_from_build_result()` to produce the structured writeback job shape for Ready for Testing planning. Use `reviewed_delivery_jobs_from_build_result()` to produce reviewed delivery handoff jobs for the Update Set XML and test evidence bundle.

Unsuccessful builds must include failure evidence through `failure_reasons` or `message`. They can produce writeback jobs that route the story to human review, but they cannot produce reviewed delivery jobs.

Use `process-external-build-result` to convert a build result file into downstream job files without calling ServiceNow:

```bash
python3 -m jedi_devproject.cli process-external-build-result \
  --result-file artifacts/external-build-results/build-20260513-010.json \
  --from-state "Work in Progress" \
  --run-id external-build-20260513-010 \
  --writeback-job-root artifacts/writeback-jobs \
  --delivery-job-root artifacts/reviewed-delivery-jobs
```

Successful build results write one structured writeback job and reviewed delivery jobs for the Update Set XML and test evidence bundle. Failed or blocked build results write only the writeback job so downstream orchestration can record the failure without pretending delivery artifacts were approved.

## Artifact Handoff Contract

Not every generated artifact should become a ServiceNow attachment. Internal orchestration evidence should stay in the controlled artifact store and be referenced by structured fields, lifecycle manifests, or artifact links.

internal audit evidence:

- implementation packet
- implementation candidate
- lifecycle manifest
- writeback audit

These artifacts should not be attached to the story by default. They can be linked for traceability, but they are not the work product testers need.

Delivery evidence:

- Approved Update Set XML
- Test Evidence Bundle

These artifacts can be attached to the story after human approval or generated test evidence approval. They are the artifacts a tester, reviewer, or release coordinator may need from ServiceNow. This attachment stage happens after candidate review/export, not during implementation packet generation or Ready for Testing writeback.

Use `plan-artifact-handoff` to produce a write-once handoff report for a story:

```bash
python3 -m jedi_devproject.cli plan-artifact-handoff \
  --run-id handoff-20260513-001 \
  --story-number STRY0010013 \
  --jobs-file artifacts/artifact-handoff-jobs.json \
  --report-root artifacts/artifact-handoff-reports
```

The jobs file is a JSON list:

```json
[
  {
    "artifact_kind": "implementation_candidate",
    "artifact_path": "artifacts/implementation-candidates/run/STRY0010013.json",
    "approved_for_delivery": false
  },
  {
    "artifact_kind": "update_set_xml",
    "artifact_path": "artifacts/exports/STRY0010013.xml",
    "approved_for_delivery": true,
    "delivery_contract": "reviewed_export"
  }
]
```

The handoff report records one decision per artifact, including `attach_to_servicenow`, `write_story_link`, `required_before_ready_for_testing`, exposure category, artifact SHA-256, delivery contract, and attachment label when applicable. The command reads each referenced artifact before writing the report; missing files fail closed. It is a planning artifact only; it does not attach files to ServiceNow.

`approved_for_delivery=true` is not sufficient by itself for live attachment. Delivery attachments also require `delivery_contract=reviewed_export`. The local delivery smoke runner uses `delivery_contract=smoke_placeholder`, which proves the planning path but intentionally does not create an attachable delivery artifact.

Use `review-delivery-artifact` to create the reviewed handoff job for a real exported delivery artifact:

```bash
python3 -m jedi_devproject.cli review-delivery-artifact \
  --run-id reviewed-export-20260513-001 \
  --story-number STRY0010013 \
  --artifact-kind update_set_xml \
  --artifact-path artifacts/exports/STRY0010013.xml \
  --reviewer-id release-coordinator \
  --job-root artifacts/reviewed-delivery-jobs
```

The command writes a write-once JSON jobs file with `approved_for_delivery=true`, `delivery_contract=reviewed_export`, `reviewer_id`, and `artifact_sha256`. Feed that jobs file into `plan-artifact-handoff` to produce the attachable handoff report. Smoke placeholder XML is rejected and cannot be promoted into a reviewed export. Update Set XML must contain a `sys_update_xml` entry; empty unload files fail closed with `reason=reviewed_export_artifact_required`.

Use `write-artifact-handoff-summary` to write a short ServiceNow work note that links the handoff report back to the story:

```bash
python3 -m jedi_devproject.cli write-artifact-handoff-summary \
  --env-file .env \
  --report-file artifacts/artifact-handoff-reports/handoff-20260513-001.json
```

The command is dry-run by default. To write the work note, pass `--apply`, `--confirm-story-number`, and `--actor-id`:

```bash
python3 -m jedi_devproject.cli write-artifact-handoff-summary \
  --env-file .env \
  --report-file artifacts/artifact-handoff-reports/handoff-20260513-001.json \
  --apply \
  --confirm-story-number STRY0010013 \
  --actor-id svc-jedi-orchestrator
```

This command writes only `work_notes`. It does not attach files, change story state, or modify structured AI fields.

Use `attach-delivery-artifacts` only after the handoff report marks delivery evidence as attachable:

```bash
python3 -m jedi_devproject.cli attach-delivery-artifacts \
  --env-file .env \
  --report-file artifacts/artifact-handoff-reports/handoff-20260513-001.json
```

The command is dry-run by default and prints the number of planned delivery attachments. To attach approved files, pass `--apply`, `--confirm-story-number`, `--actor-id`, `--audit-root`, and `--run-id`:

```bash
python3 -m jedi_devproject.cli attach-delivery-artifacts \
  --env-file .env \
  --report-file artifacts/artifact-handoff-reports/handoff-20260513-001.json \
  --apply \
  --confirm-story-number STRY0010013 \
  --actor-id svc-jedi-orchestrator \
  --audit-root artifacts/delivery-attachment-audit \
  --run-id attach-delivery-20260513-001
```

The command attaches only decisions where `attach_to_servicenow=true`. Internal evidence remains link-only. Delivery files use the ServiceNow Attachment API and are uploaded to the `rm_story` record without changing state or structured AI fields.

Apply writes a local write-once attachment audit record. The audit includes the story number, actor id, handoff report path, delivery artifact paths, labels, and ServiceNow attachment sys_ids returned by the Attachment API. It does not include the ServiceNow story sys_id.

Before apply calls ServiceNow, `attach-delivery-artifacts` recalculates each delivery file hash and compares it to the handoff report `artifact_sha256`. A missing file fails closed with `reason=artifact_missing`; a changed file fails closed with `reason=artifact_hash_mismatch`; no attachment is uploaded in either case. Dry-run attachment planning also verifies the same hashes before reporting planned attachments. The attachment audit records the reviewed `artifact_sha256` for each uploaded file.

Use `run-delivery-artifact-smoke` to exercise the delivery handoff and attachment planning path without a real Update Set exporter:

```bash
python3 -m jedi_devproject.cli run-delivery-artifact-smoke \
  --run-id delivery-smoke-20260513-001 \
  --story-number STRY0010013 \
  --artifact-root artifacts/delivery-smoke
```

The command creates an XML-shaped placeholder Update Set artifact, writes a handoff report with `delivery_contract=smoke_placeholder`, and prints the planned attachment count. It does not call ServiceNow and does not attach files. This smoke path validates orchestration only; it is not a substitute for a real reviewed Update Set export.

Use `run-reviewed-delivery-smoke` to exercise the approved local delivery path without ServiceNow mutation:

```bash
python3 -m jedi_devproject.cli run-reviewed-delivery-smoke \
  --run-id reviewed-delivery-smoke-20260513-001 \
  --story-number STRY0010013 \
  --reviewer-id release-coordinator \
  --artifact-root artifacts/reviewed-delivery-smoke
```

The command creates a non-placeholder XML fixture, writes a reviewed delivery job with `delivery_contract=reviewed_export`, writes the handoff report, writes a manifest under `reviewed-delivery-lifecycle-manifests`, and prints one planned delivery attachment. It does not call ServiceNow and does not attach files.

The reviewed delivery lifecycle manifest references the delivery artifact, reviewed delivery job, and handoff report by path and SHA-256. It also records the dry-run `delivery_attachment_plan`. It does not include ServiceNow sys_ids.

Batch orchestration should use `run_writeback_batch()`. It runs capability preflight once, fails the batch closed when the instance is not ready, and returns a summary with total, allowed, applied, idempotent, and blocked counts.

For file-based orchestration, provide a writeback job file:

```json
[
  {
    "story_number": "STRY0010013",
    "build_reference": "build-20260513-001",
    "artifact_url": "artifacts/STRY0010013.json",
    "from_state": "Ready"
  }
]
```

Run it with:

```bash
python3 -m jedi_devproject.cli run-writeback-batch \
  --env-file .env \
  --jobs-file artifacts/writeback-jobs.json \
  --apply \
  --actor-type service \
  --actor-id svc-jedi-orchestrator \
  --execution-id run-20260513-001 \
  --audit-root artifacts/writeback-audit \
  --batch-report-root artifacts/writeback-batches
```

Empty job files are rejected. Each job defaults to a successful external build result unless `build_status` is provided.

Each batch writes a write-once batch report artifact named after `--execution-id`. The report includes capability status, summary counts, and per-story outcome records. It does not include ServiceNow sys_ids.
