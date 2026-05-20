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

The runtime uses PostgreSQL for durable operational state and DB-backed JSON artifacts. PostgreSQL is the MVP store for lifecycle orchestration because the API and worker runtime need production-shaped transactions, foreign keys, JSONB event payloads, row-level worker claims, and durable artifact records from the start.

The operational schema is defined in `db/migrations/0001_operational_store.sql` and initialized by `connect_operational_store(database_url=...)` in `jedi_devproject.operational_store`. It includes:

- `lifecycle_events`: inbound ServiceNow lifecycle events and their preserved original payload.
- `fulfillment_jobs`: one idempotent fulfillment job per lifecycle event, including status, attempt count, and worker lock metadata.
- `job_events`: append-only status history for queued, running, completed, blocked, or failed job transitions.
- `artifact_blobs`: durable JSON artifacts such as implementation packets and implementation candidates, stored with schema version, SHA-256 hash, story number, and job id.
- `artifact_refs`: stable artifact references with SHA-256 hashes. DB-backed artifacts use `db://artifact_blobs/<id>` paths and keep the `artifact_id` relation populated.

The current claim primitive is `claim_next_fulfillment_job(worker_id=...)`. It uses `SELECT ... FOR UPDATE SKIP LOCKED` inside a PostgreSQL transaction to select the oldest queued job, mark it `running`, increment the attempt count, and set `locked_by` and `locked_at`. API and worker processes should use this store instead of treating JSON files as a queue.

## Lifecycle Webhook API

The local runtime exposes a FastAPI application from `create_lifecycle_api()` in `jedi_devproject.lifecycle_api`. Production wiring must provide `DATABASE_URL` for `connect_operational_store(database_url=...)`, then inject that store into the API factory.

The lifecycle receiver is:

```text
POST /lifecycle/events
```

A valid `Draft` to `Ready` `LifecycleStateChangeEvent` returns `202 Accepted`, records the event in `lifecycle_events`, enqueues one `fulfillment_jobs` row, and returns the queued `job_id`. A valid `Ready for Testing` to `Complete` event records the event, writes a `story_completed` audit entry against the latest fulfillment job for that story, and updates the story `u_ai_status=Complete` by `story_sys_id` without enqueueing another build. A valid `Ready for Testing` to `Ready` event records `rework_requested` against the latest fulfillment job without enqueueing another build. A valid `Ready for Testing` to `Draft` event marks the latest fulfillment job `rejected` and preserves artifacts for audit instead of deleting evidence. Unsupported lifecycle transitions are still accepted and recorded, but they are not enqueued for fulfillment.

The webhook request path does not execute fulfillment inline. Build evaluation, ServiceNow claim writeback, implementation packet generation, external build handoff, and Ready for Testing writeback must run in worker processing after a queued job is claimed.

### Lifecycle Webhook Authentication

The runtime has an explicit lifecycle webhook auth boundary. `JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE=disabled` is accepted only when `JEDI_ENVIRONMENT=development`; any non-development runtime fails closed with `503` until webhook authentication is configured.

For production-shaped deployments, start with timestamped HMAC request signing:

```text
JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE=hmac_sha256
JEDI_LIFECYCLE_WEBHOOK_SECRET=<shared signing secret>
JEDI_LIFECYCLE_WEBHOOK_MAX_SKEW_SECONDS=300
```

Signed lifecycle calls must include:

```text
X-JEDI-Webhook-Timestamp: <unix epoch seconds>
X-JEDI-Webhook-Signature: sha256=<hex hmac>
```

The signature base string is `<timestamp>.<raw request body>`, signed with `HMAC-SHA256` using `JEDI_LIFECYCLE_WEBHOOK_SECRET`. The receiver verifies the timestamp replay window before validating the event payload and rejects missing signatures with `401` and bad signatures with `403`. The receiver accepts `sha256=<hex hmac>` for generic clients and `sha256-base64=<base64 hmac>` for ServiceNow emitters because ServiceNow's `GlideCertificateEncryption.generateMac()` returns Base64 MAC output.

`shared_secret` is available only as a simpler interim mode using `X-JEDI-Webhook-Secret`; it is not replay-resistant and should not be the Federal production posture. `servicenow_oauth` is reserved and currently fails closed with `501` until the OAuth validation path is designed and tested.

## Artifact Retrieval API

Runtime artifact reads are admin-only. Set `JEDI_ADMIN_API_TOKEN` in the API service environment and call artifact endpoints with:

```text
Authorization: Bearer <JEDI_ADMIN_API_TOKEN>
```

The artifact read endpoints are:

```text
GET /artifacts/{artifact_id}
GET /jobs/{job_id}/artifacts
GET /admin/lifecycle-events
GET /admin/jobs
```

`GET /artifacts/{artifact_id}` returns artifact metadata plus the JSON payload stored in `artifact_blobs`. It returns `404` when the artifact id is not found. `GET /jobs/{job_id}/artifacts` returns only the artifact references for the requested job, including `artifact_id`, `artifact_kind`, `path`, and SHA-256 hash.

`GET /admin/lifecycle-events` returns the most recent lifecycle event summaries with event id, event type, story number, received timestamp, and validation status. It intentionally does not return raw event payload JSON or ServiceNow sys_ids. `GET /admin/jobs` returns the most recent fulfillment job summaries with status, attempt count, lock metadata, and the latest error text.

These endpoints do not replace ServiceNow as the work surface. They provide a safe API for the admin GUI and operator diagnostics to inspect generated implementation packets and candidates. Lifecycle webhook calls do not use this admin token, and unauthenticated artifact reads are rejected.

## Admin Console

The hosted API serves a read-only browser console at:

```text
GET /admin
```

Configure local Basic auth credentials in the API service environment:

```text
JEDI_ENVIRONMENT=development
JEDI_ADMIN_AUTH_MODE=dev_basic
JEDI_ADMIN_CONSOLE_USERNAME=<operator username>
JEDI_ADMIN_CONSOLE_PASSWORD=<strong password>
```

The console shows recent fulfillment jobs, recent lifecycle events, and Basic-auth artifact detail pages under `/admin/artifacts/{artifact_id}`. It does not expose raw lifecycle event payload JSON or ServiceNow sys_ids in the dashboard. It also does not provide retry, reject, rebuild, preview, commit, or other mutation actions; ServiceNow remains the work surface and update set preview/commit remains the human review point.

`dev_basic` is development-only. The default `JEDI_ADMIN_AUTH_MODE=disabled` fails closed, and the runtime rejects `dev_basic` unless `JEDI_ENVIRONMENT=development`. Reserved production modes are `oidc` and `servicenow_oauth`; both fail closed until implemented. See `docs/admin-auth-config.md` for the required OIDC and ServiceNow OAuth configuration details.

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

Optional values are `JEDI_WORKER_ID`, `JEDI_BUILD_CLAIM_APPLY`, `JEDI_BUILD_CLAIM_FROM_STATE`, `JEDI_BUILD_CLAIM_STATE`, `JEDI_CLASSIFIER_GATE`, `JEDI_ADMIN_API_TOKEN`, `JEDI_ENVIRONMENT`, `JEDI_ADMIN_AUTH_MODE`, `JEDI_ADMIN_CONSOLE_USERNAME`, and `JEDI_ADMIN_CONSOLE_PASSWORD`. The API process should call `create_runtime_api()` with these settings. The worker process should call `process_one_runtime_fulfillment()` in a loop or scheduler owned by the runtime host.

`JEDI_CLASSIFIER_GATE` defaults to `true`. When `true`, the worker keeps the normal fail-closed classifier gate: unknown or unsupported story surfaces do not call the model and receive human-review feedback. Setting `JEDI_CLASSIFIER_GATE=false` is an experimental development control that lets unknown classifier outcomes call the model for exploratory structured reasoning. It does not enable automatic retrieved Update Set handoff for those stories; non-automated classifier outcomes remain `Human Review Required`.

For ServiceNow Table API integrations, prefer state values over labels. In the current PDI, `Ready` is `1` and `Work in progress` is `2`, so the Railway worker uses `JEDI_BUILD_CLAIM_FROM_STATE=1` and `JEDI_BUILD_CLAIM_STATE=2`.

`runtime_worker.run_loop()` provides the built-in polling loop for hosts that run the worker as a long-lived process. It repeatedly calls the same one-job runtime processor, sleeps after idle polls, and can stop on the first failed job for smoke tests or continue when the host owns failure alerting.

Runtime fulfillment failures write back to the originating ServiceNow story work notes through the worker `failure_notifier`. The note begins with `Automated fulfillment failed` and includes the lifecycle event id, fulfillment job id, and redacted failure message. If the ServiceNow writeback itself fails, the worker still marks the PostgreSQL job failed and stores both the original handler error and the notifier error in `last_error`.

### Audit Correlation

The runtime audit trail starts with the ServiceNow lifecycle payload `correlation_id`. Operational views carry that id forward from the canonical lifecycle event payload instead of duplicating mutable trace identifiers across derived tables.

The operator trace path is:

```text
lifecycle event -> fulfillment job -> job events -> artifact refs
```

Use the story number plus `correlation_id` to connect ServiceNow work notes, the `/admin/lifecycle-events` response, the `/admin/jobs` response, artifact references, and retrieved Update Set handoff notes. The admin job and lifecycle event views include the correlation id, and the browser admin console renders it beside the story and job/event ids.

Admin diagnostics remain minimized. Raw lifecycle payload JSON is not returned by list views, ServiceNow sys_ids are not shown in the dashboard, and diagnostic database URL passwords are redacted before `last_error` is returned by admin job views.

### Rate Limits and Payload Bounds

The hosted API applies bounded request handling before expensive processing:

- Lifecycle webhook bodies over `JEDI_LIFECYCLE_WEBHOOK_MAX_BODY_BYTES` are rejected with `413`.
- Lifecycle webhook bursts over `JEDI_LIFECYCLE_RATE_LIMIT_MAX_REQUESTS` within `JEDI_LIFECYCLE_RATE_LIMIT_WINDOW_SECONDS` are rejected with `429`.
- Admin JSON endpoints use `JEDI_ADMIN_RATE_LIMIT_MAX_REQUESTS` and `JEDI_ADMIN_RATE_LIMIT_WINDOW_SECONDS` and return `429` when exceeded.
- Admin list endpoints cap requested limits at 100 rows even when callers request a larger value.

Defaults are intentionally conservative for the PDI/Railway MVP: lifecycle webhooks allow 64 KiB bodies, 60 lifecycle calls per 60 seconds, and 120 admin calls per 60 seconds. These controls are a per-process MVP control. They are not a distributed Federal production abuse-control boundary. Production should also enforce request size, request rate, IP reputation, and alerting at an edge, WAF, or API gateway layer approved by the customer environment.

### Production Runtime Fail-Closed Checklist

Production API and worker entrypoints call `validate_runtime_settings()` before opening the operational store or processing work. Development can run with local defaults, but `JEDI_ENVIRONMENT=production` fails closed unless the runtime posture is explicit.

Production requirements:

- `JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE=hmac_sha256`
- `JEDI_LIFECYCLE_WEBHOOK_SECRET=<shared signing secret>`
- `JEDI_MODEL_PROVIDER=openai`
- `OPENAI_API_KEY=<provider key>`
- `OPENAI_MODEL=<approved model id>`

`JEDI_ADMIN_AUTH_MODE=dev_basic` is rejected in production. `JEDI_ADMIN_AUTH_MODE=disabled` is also rejected for the API runtime because the hosted app exposes `/admin`. Reserved production admin modes `oidc` and `servicenow_oauth` remain fail-closed until their token validation, session handling, and authorization checks are implemented.

### Secret Inventory

| Secret | Location | Purpose | Rotation Path |
|---|---|---|---|
| `SERVICENOW_CLIENT_SECRET` | API and worker runtime env | ServiceNow OAuth client credentials for Table API operations | Rotate the ServiceNow OAuth app secret, update runtime env, redeploy API and worker |
| `JEDI_LIFECYCLE_WEBHOOK_SECRET` | API runtime env | HMAC validation for inbound lifecycle events | Generate a new random value, update API env and ServiceNow `x_jedi.lifecycle.webhook.secret`, then redeploy/retest signed webhook calls |
| `x_jedi.lifecycle.webhook.secret` | ServiceNow system property | HMAC signing secret read by the lifecycle Business Rule emitter | Match `JEDI_LIFECYCLE_WEBHOOK_SECRET`; update out of band and do not place the value in bootstrap artifacts |
| `OPENAI_API_KEY` | Worker runtime env | ChatGPT/OpenAI model execution | Rotate in the approved OpenAI project, update worker env, redeploy worker, and run a model smoke story |
| `JEDI_ADMIN_CONSOLE_PASSWORD` | API runtime env, development only | Local Basic auth for `/admin` during development | Replace with a strong temporary value when needed; do not use with `JEDI_ENVIRONMENT=production` |
| `JEDI_ADMIN_API_TOKEN` | API runtime env | Bearer token for JSON artifact/admin diagnostic API endpoints | Rotate by updating the API env and all approved operator clients |

## ChatGPT Implementation Adapter

`OpenAIResponsesProvider` in `jedi_devproject.openai_provider` is the first ChatGPT/OpenAI adapter boundary for implementation candidate generation. It calls the OpenAI Responses API with strict JSON schema output and returns the existing internal implementation candidate shape.

The model-facing schema requires ServiceNow field mutations as explicit `name/value` pairs. The adapter normalizes those pairs into the internal `fields` dictionary after parsing. Arbitrary field objects fail closed at the provider boundary so model output cannot bypass the implementation packet and writeback validators.

Runtime OpenAI use is disabled unless `JEDI_MODEL_PROVIDER=openai` is set. `OPENAI_API_KEY` and `OPENAI_MODEL` must also be present when that provider is enabled. Having `OPENAI_API_KEY` in the host environment does not by itself activate model calls.

When OpenAI runtime mode is enabled, fulfillment first runs the guarded build-claim path, then `model_candidate_fulfillment_handler` builds an `instance_context_bundle`, builds a structured `context_dossier` inside the `implementation_packet`, calls `OpenAIResponsesProvider` only when required context is sufficient, validates the model response, and returns DB-ready JSON artifacts for the context bundle, implementation packet, and implementation candidate. The worker stores those artifacts in `artifact_blobs`, records DB-backed `artifact_refs`, and writes a ServiceNow work note keyed to the fulfillment job id. The model stage does not apply model-generated platform changes.

The model-facing dossier can include read-only XML shape references for the selected ServiceNow surface. These references are structured field/record models, not raw `sys_update_xml` payloads, and the model output contract is `structured_candidate_change_only`. Model responses that include raw XML fields or raw Update Set XML content fail validation.

Before model generation, the worker investigates the target ServiceNow surface. This is broader than table/form metadata. Depending on story signals, the `instance_context_bundle` can include table schema, form layout, Business Rules, Client Scripts, UI Policies, Flow Designer records, Script Includes, ACL indicators, CMDB/discovery indicators, outbound REST integration surfaces, and public documentation queries routed through the approved RAG boundary.

The worker uses read-only Table API retrieval for live instance surfaces and does not call public documentation sites directly at runtime. Public documentation context must come through curated or approved RAG sources with citations. If required context cannot be retrieved, the implementation packet records `context_sufficiency.status=insufficient`, the provider is not called, and the story receives human-review or clarification feedback rather than a guessed implementation.

Each surface context includes a confidence score and citation records with source table, query, and retrieved record count. Surface artifacts intentionally minimize executable or sensitive material: script bodies and conditions are replaced with redaction markers, ServiceNow sys_ids are not preserved in the model-facing bundle, and integration endpoint query strings are redacted. When context blocks model execution, the ServiceNow work note names the missing surface context directly.

## Capability-Based Automation Gate

The capability-based automation gate is not table-based. In this gate, table names are metadata for risk, discovery, and validation; they are not allowlist gates by themselves.

The baseline supported implementation capability is generic dictionary field creation plus form placement:

- `dictionary_field_create`
- `field_label_create`
- `form_layout_place_field`

For example, `STRY0010001` classifies as an automated Incident dictionary/form change for `incident.u_antics` when the story describes the target table, field label, string type, length, and placement below Description.

Static form section edits are recognized separately from UI Policy behavior. The `form_section_remove` capability covers narrow stories such as hiding or removing named tabs/sections from an existing form layout, including the Demand example that asks for the Assessment and Financials tabs to be removed from `dmn_demand`. The worker retrieves `form_sections` and `form_layout`, stores a `form-layout-analysis-v1` artifact, includes structured XML shape references in the dossier, and calls the model for structured candidate reasoning. Because the form-section Update Set builder is not mature enough for automated handoff, the structured candidate is preserved as an artifact and routed to human review instead of importing a retrieved Update Set.

Structured form-section stories must either use an explicit artifact type such as `Form Section Removal` or use `Form Section` with an action that clearly says to remove, hide, or not display the named sections. Generic form-section requests to rename, add, reorder, script, role-gate, or otherwise transform a tab are not treated as deletion requests and route away from this builder.

Form layout automation now uses a surface-operation planning boundary. The intent parser identifies the `form_layout` surface and the requested outcome; the surface planner maps that intent to operation names such as `form_layout.section.remove`, `form_layout.section.add`, `form_layout.section.rename`, and `form_layout.section.reorder`. Known form-layout operations can still be reasoned about by the model when context is sufficient. Builder maturity only affects confidence and fulfillment routing: immature builders lower confidence and block retrieved Update Set handoff until their XML evidence and validators are approved.

Stories that are clear but require unsupported capabilities such as `acl_modify`, `flow_modify`, `business_rule_create`, `data_migration`, or `integration_modify` receive human-review feedback naming the unsupported capability. Stories missing required details receive clarification feedback through `u_ai_status=Needs Clarification` and a work note naming the missing details. Any non-automated candidate may also include general automation feedback and a `Suggested rewrite:` block. The rewrite guidance is capability-agnostic: it tells the requester how to restate the story with target artifact type, target surface, fields or records read, fields or records changed, constraints, expected behavior, test evidence, and rollback expectation so a later run has a better chance of being automated or cleanly routed to analysis/manual build.

After a dictionary/form implementation candidate artifact is durably stored, the worker generates reviewed Update Set XML for `JEDI <story number> - AI Candidate` and posts it to the ServiceNow-side importer `jedi_update_set_import`. The XML contains a `sys_remote_update_set` header and candidate customer updates linked through `remote_update_set`, never through a local `update_set`. After import, the worker looks up the retrieved update set by `remote_sys_id`, discovers the active `Ready for Testing` state choice for `rm_story`, and updates the story with `state=<Ready for Testing value>`, `u_ai_status=Ready for Testing`, `u_ai_handoff_type=retrieved_update_set`, `u_ai_handoff_reference=<retrieved update set sys_id>`, `u_ai_artifact_reference=<candidate artifact ref>`, and a work note containing a direct `sys_remote_update_set.do?sys_id=...` link.

This retrieved Update Set is the ServiceNow-native review surface. It is not automatically committed and it does not mutate `sys_dictionary`, `sys_ui_element`, or local `sys_update_set` records during fulfillment. Reviewers must preview, scan, resolve, and commit the retrieved Update Set inside ServiceNow. The story entering Ready for Testing means the automated handoff is ready for human test/review; it does not mean the retrieved Update Set has been approved or committed. `JEDI_UPDATE_SET_APPLY` is retained only as a backward-compatible runtime setting; generated implementation candidates now use the retrieved Update Set handoff path and do not perform local apply-under-update-set mutation.

If the deterministic packet gates produce a non-automated candidate, or if model reasoning succeeds but builder maturity is below the automated handoff threshold, the worker stores the implementation packet and candidate artifacts, writes either `u_ai_status=Needs Clarification` or `u_ai_status=Human Review Required`, writes a story work note with the candidate artifact reference and eligibility reasons, and does not create a retrieved Update Set.

If the candidate contains unsupported changes, the importer endpoint is missing, the imported retrieved Update Set cannot be found by `remote_sys_id`, or the active `Ready for Testing` state choice cannot be discovered, the job fails and writes the failure back to story work notes. Runtime failure notification also discovers the active `Draft` state choice; when found, it sets `state=<Draft value>` and `u_ai_status=Automation Failed` so failed automation does not leave the story in Work in Progress with `Build In Progress`. The previous local-apply path is kept in code only as a legacy utility and must not be used for automated candidate fulfillment.

### Capability Extension Model

New ServiceNow build surfaces must be introduced through the Capability Extension Contract, not by adding one-off provider prompts. Each supported capability has a versioned `CapabilityProfile` in the capability registry.

A `CapabilityProfile` must name its supported artifacts, UAT story shape, required context surfaces through `required_instance_context`, model packet schema, output validators, deterministic validators, unsupported cases, retrieved Update Set evidence, and tests. The runtime may call a model only after deterministic story analysis selects an active profile, the investigator retrieves the required context surfaces, and the profile's validators are available. If any of those conditions fail, the story routes to clarification or human review.

### Capability Maturity Model

Each `CapabilityProfile` carries both `current_max_story_points` and `target_max_story_points`. The full-maturity target for autonomous handling is 5 story points. A capability may still have a lower current limit, including `0`, until its researcher, deterministic validators, build_pipeline, and retrieved Update Set evidence are implemented.

The `researcher` field names the context worker responsible for gathering live ServiceNow state before model or builder execution. The `build_pipeline` field names the deterministic path that converts validated structured intent into reviewed ServiceNow artifacts. This keeps the product aimed at 5 story points without pretending every surface is currently safe to mutate.

Business Rule analysis first is the next supported implementation step. Sprint 112 should retrieve and classify current `sys_script` state, decide whether a story is a Business Rule candidate, and report missing inputs or unsupported cases without creating Business Rules. Business Rule generation can follow only after that profile proves the context and validation path.

### Flow Designer Generation Capability

The Sprint 124 Flow Designer generation profile design defines the future `flow_modify` capability. No runtime generation is enabled for Flow Designer. The profile has `current_max_story_points=0` and `target_max_story_points=5`.

Flow Designer remains context-only at runtime. Flow Designer context-only review can retrieve and summarize relevant `sys_hub_flow` records and the read-only `flow_graph` flow graph context, but generated flow mutation is unsupported until graph diff output shape, validators, and retrieved Update Set evidence are implemented.

The future supported subset is one active record-triggered flow at a time, one target table or trigger context, and either one additive action or one narrow condition change. Required context includes `flows` and `flow_graph` retrieval across approved `sys_hub_*` records such as `sys_hub_flow`, `sys_hub_trigger_instance`, `sys_hub_action_instance`, `sys_hub_flow_logic_instance_v2`, `sys_hub_trigger_input`, `sys_hub_trigger_output`, `sys_hub_action_input`, and `sys_hub_action_output`.

Required `flow_graph` retrieval fails closed when the target flow list is missing or when a flow has no trigger or action graph records. Runtime history tables remain excluded from the context worker and from any future mutation boundary.

Sprint 126 adds validation-only graph diff support for the pseudo-table `sys_hub_flow_graph_diff`. The only currently allowed diff operations are `add_action` and `update_condition`. The validator rejects raw XML, raw `sys_update_xml`, unretrieved node references, scripts, custom actions, spokes, credentials, tokens, subflows, approvals, and broad graph rewrites. No runtime generation is enabled and `sys_hub_flow_graph_diff` is not accepted by retrieved Update Set handoff.

Sprint 127 adds Flow Designer builder preflight planning. The preflight verifies `retrieved_graph_hash_matches_existing_graph_hash`, keeps `runtime_generation_enabled=false`, keeps retrieved Update Set handoff disabled, and reports `Flow Designer builder is design-only`; runtime generation remains disabled. Required evidence before implementation can proceed includes `xml_shape_repository_available`, customer update naming, flow snapshot update strategy, rollback customer update strategy, and ServiceNow preview/commit review.

Sprint 128 adds the Flow XML shape repository `flow-xml-shapes-v1`. The repository contains review metadata only for `sys_hub_flow`, `sys_hub_action_instance`, and `sys_hub_flow_logic_instance_v2` customer-update shapes. It records the `record_update` root, `INSERT_OR_UPDATE` action, required fields, forbidden fields, and shape-specific review notes. There is still no Flow XML builder and no retrieved Update Set handoff for Flow Designer.

Sprint 129 adds the Flow XML shape evidence validator `validate_flow_xml_shape_evidence`. Operators and future researchers can use it to validate retrieved review samples against `flow-xml-shapes-v1` before any builder work is considered. The validator rejects malformed XML, wrong root or action values, missing required field evidence, and forbidden field evidence. It adds `xml_shape_evidence_validator_available` to the preflight evidence list, but there is still no Flow XML builder and no retrieved Update Set handoff for Flow Designer.

Sprint 130 adds the Flow customer update strategy `flow-customer-update-strategy-v1`. The strategy uses the existing ServiceNow-style `table_sys_id` update name convention for approved Flow tables, rejects unapproved Flow tables, rejects unstable non-hex sys_ids, and records rollback strategy coverage for `add_action` and `update_condition`. This gives the future builder a reviewable naming and rollback strategy, but there is still no Flow XML builder and no retrieved Update Set handoff for Flow Designer.

Sprint 131 adds the Flow snapshot update strategy `flow-snapshot-update-strategy-v1`. The strategy requires retrieved `latest_snapshot` evidence from `sys_hub_flow`, rejects missing or unstable snapshot references, and rejects snapshot/version table mutations because snapshot table mutation is not supported in the current Flow path. This keeps future Flow builder work anchored to retrieved instance evidence, but there is still no Flow XML builder and no retrieved Update Set handoff for Flow Designer.

Sprint 132 adds the Flow preview/commit review strategy `flow-preview-commit-review-strategy-v1`. The strategy names the human review boundary as `retrieved_update_set_preview_commit`, requires preview before commit, requires human commit, and rejects auto-commit because Flow Designer auto-commit is not supported. This keeps ServiceNow preview/commit as the review point, but there is still no Flow XML builder and no retrieved Update Set handoff for Flow Designer.

Sprint 133 adds the Flow builder readiness contract `flow-builder-readiness-v1`. The contract aggregates required Flow builder evidence into one auditable object, reports `missing_evidence`, and keeps both runtime generation and retrieved Update Set handoff disabled with the blocked reason `Flow Designer builder is not implemented`. This is still no Flow XML builder and no retrieved Update Set handoff for Flow Designer.

Sprint 134 adds Flow builder plan readiness wiring. Every Flow builder preflight plan now includes `readiness_contract_version`, `missing_builder_evidence`, `ready_for_runtime_generation=false`, `ready_for_retrieved_update_set_handoff=false`, and the readiness blocked reason. This keeps preflight consumers from treating a design-only plan as an implementation-ready builder. There is still no Flow XML builder and no retrieved Update Set handoff for Flow Designer.

Sprint 135 adds Flow unsupported reason codes. The readiness contract and every Flow builder preflight plan now include `unsupported_reason_codes` for routing and admin display. Current codes are `flow_builder_not_implemented`, `runtime_generation_disabled`, and `retrieved_update_set_handoff_disabled`. These codes do not enable mutation; there is still no Flow XML builder and no retrieved Update Set handoff for Flow Designer.

Sprint 136 adds Flow unsupported reason guidance. The readiness contract and every Flow builder preflight plan now include `unsupported_reason_guidance`, with stable summaries, the `route_to_human_review` operator action, and ServiceNow work note text. This gives operators actionable feedback without duplicating unsupported Flow prose in worker or admin code. There is still no Flow XML builder and no retrieved Update Set handoff for Flow Designer.

Sprint 137 adds the Flow preflight guidance artifact. When fulfillment sees `flow_modify`, the worker now stores a `flow_preflight_guidance` artifact with schema `flow-preflight-guidance-v1`, the `flow-builder-readiness-v1` disabled readiness flags, `unsupported_reason_codes`, and `unsupported_reason_guidance` including `route_to_human_review`. This makes Flow routing guidance visible in persisted runtime evidence while preserving the boundary: no Flow XML builder and no retrieved Update Set handoff for Flow Designer.

Sprint 138 adds the Flow preflight guidance work note. After artifacts are persisted, unsupported Flow stories still move to `u_ai_status=Human Review Required`, but the ServiceNow work note now includes `Flow preflight guidance artifact`, the `flow_preflight_guidance` artifact reference, and the `route_to_human_review` work-note guidance from the readiness contract. This makes the ServiceNow user surface actionable without creating a retrieved Update Set. There is still no Flow XML builder and no retrieved Update Set handoff for Flow Designer.

Unsupported behavior includes graph rewrites, custom actions, spokes and integrations, credentials, secrets, tokens, API keys, subflows, approval orchestration, script steps, data migration, runtime execution history mutation, and direct mutation of Flow runtime state outside reviewed customer updates.

### Code Surface Analysis Capability

The `business_rule_analyze`, `client_script_analyze`, and `script_include_analyze` capabilities are context-only. They exist to inspect stories that appear to need ServiceNow code-surface work and retrieve the current platform records before any generation capability is approved.

Surface mappings:

- Business Rule analysis retrieves `sys_script`.
- Client Script analysis retrieves `sys_script_client`.
- Script Include analysis retrieves `sys_script_include`.

When selected, the runtime retrieves the required context, redacts script-like fields, stores an `instance_context_bundle`, and stores a `code-surface-analysis-v1` artifact. The analysis names the capability, surface, source table, target table or `global`, existing record count, unsupported cases, and context sufficiency. It does not call the model and does not create a retrieved Update Set.

The story receives human-review feedback through the normal work-note path. Code surface generation remains unsupported until separate mutation profiles define output schema, deterministic validators, retrieved Update Set XML evidence, and UAT expectations for each artifact type.

### Business Rule Generation Capability

`business_rule_generate` is enabled for the first production-hardening subset. The current maturity limit is `current_max_story_points=3`; the full maturity target remains `target_max_story_points=5`.

The supported subset is table-local Business Rules only: `before/after` timing, `insert/update` operations, one target table, one generated rule, and an explicit condition. Generated changes must become `sys_script` customer updates wrapped in `sys_update_xml` for retrieved Update Set review. Retrieved Update Set preview/commit remains the human review boundary.

Unsupported behavior includes delete rules, async/display rules, scheduled jobs, ACL changes, Script Include creation, no outbound REST or SOAP calls, no credentials or endpoint construction, no cross-table writes, no broad GlideRecord mutation, and no system-table mutation outside the intended `sys_script` customer update.

The provider output must be structured implementation intent, not authoritative XML. Required fields include target table, rule name, timing, operations, condition summary, condition expression, script body, fields read, fields written, test plan, rollback notes, and reviewer notes. Deterministic validators approve table context, operation scope, script safety, field access, secret detection, and parseable `sys_update_xml` before a retrieved Update Set can be imported. Scripts containing forbidden tokens such as `GlideRecord`, destructive update/delete APIs, outbound HTTP/S endpoints, credential access, passwords, tokens, or API keys fail closed before import.

### Client Script Generation Capability

The Sprint 117 Client Script Generation Profile Design is implemented for the first production-hardening subset. `client_script_generate` is enabled with `current_max_story_points=3`; the full maturity target remains `target_max_story_points=5`.

The supported subset is table-local Client Scripts only: one generated `sys_script_client` record on one target table, `onLoad`, `onChange`, or `onSubmit` type, optional target field for `onChange`, and behavior implemented through ServiceNow client APIs such as `g_form`. Generated changes must become `sys_script_client` customer updates wrapped in `sys_update_xml` for retrieved Update Set review. Retrieved Update Set preview/commit remains the human review boundary.

Unsupported behavior includes DOM manipulation outside g_form APIs, `document` or `window` access, browser storage, `fetch` or `XMLHttpRequest`, endpoint construction, credentials, secrets, tokens, API keys, GlideAjax dependency creation, Script Include creation, ACL changes, integrations, cross-table writes, and system-table mutation outside the intended `sys_script_client` customer update.

The provider output must be structured implementation intent, not authoritative XML. Required fields include target table, script name, Client Script type, target field for `onChange`, condition summary, script body, fields read, fields written, messages shown, test plan, rollback notes, and reviewer notes. Deterministic validators approve table context, script type, target field, allowed client APIs, field access, secret detection, and parseable `sys_update_xml` before a retrieved Update Set can be imported. Any forbidden Client Script behavior fails closed before import.

### Script Include Generation Capability

The Sprint 119 Script Include Generation Profile Design is implemented for the first production-hardening subset. `script_include_generate` is enabled with `current_max_story_points=3`; the full maturity target remains `target_max_story_points=5`.

The supported subset is server-side utility Script Includes only: one generated `sys_script_include` record per story, one named class or function, explicit scope, explicit client-callable decision, and no simultaneous caller creation. Generated changes must become `sys_script_include` customer updates wrapped in `sys_update_xml` for retrieved Update Set review.

Unsupported behavior includes global privilege escalation, cross-scope access changes, role changes, ACL changes, system property changes, credentials, secrets, tokens, API keys, outbound REST/SOAP/email/event calls, broad GlideRecord mutation, data migration, background repair logic, and any Script Include that requires simultaneous Business Rule, Client Script, Flow, scheduled job, or integration creation.

client callable Script Includes are not supported in the first implementation because that would also require GlideAjax caller design. The provider output must be structured implementation intent, not authoritative XML. Required fields include Script Include name, API name, scope, client-callable flag, active flag, description, script body, public methods, tables read, tables written, fields read, fields written, test plan, rollback notes, and reviewer notes. Deterministic validators approve identifier shape, retrieved Script Include context, script safety, caller boundary, secret detection, and parseable `sys_update_xml` before a retrieved Update Set can be imported. Any forbidden Script Include behavior fails closed before import.

### UI Policy Generation Capability

The Sprint 122 UI Policy Generation Profile Design is implemented for the first production-hardening subset. `ui_policy_generate` is enabled with `current_max_story_points=3`; the full maturity target remains `target_max_story_points=5`.

The supported future subset is declarative, table-local UI Policy behavior only: one generated `sys_ui_policy` record and one or more generated `sys_ui_policy_action` records, an explicit target table, an explicit condition, an explicit reverse-if-false decision, and field actions limited to mandatory, visible, or read-only behavior. Generated changes must become `sys_ui_policy` and `sys_ui_policy_action` customer updates wrapped in `sys_update_xml` for retrieved Update Set review.

Unsupported behavior includes run scripts, advanced scripts, Client Script behavior, `g_form` logic, Business Rule creation, Script Include creation, Flow creation, ACL changes, integration calls, cross-table behavior, data migration, role changes, system property changes, credentials, secrets, tokens, and API keys.

The provider output must be structured implementation intent, not authoritative XML. Required fields include target table, policy name, condition, reverse-if-false decision, run-scripts flag, view, fields read, UI Policy actions, test plan, rollback notes, and reviewer notes. Deterministic validators approve table context, form layout context, existing UI Policy context, condition fields, action fields, run-scripts disabled state, forbidden token checks, and parseable `sys_update_xml` before a retrieved Update Set can be imported. Any forbidden UI Policy behavior fails closed before import.

## CI/CD Update Set API Capability

Use `check-cicd-update-set-capability` to verify that the target ServiceNow instance exposes the Yokohama+ CI/CD Update Set API before designing promotion around it:

```bash
python3 -m jedi_devproject.cli check-cicd-update-set-capability --env-file .env
```

The command is read-only. It sends non-mutating `POST /api/sn_cicd/update_set/create` and `POST /api/sn_cicd/update_set/retrieve` probes without the required parameters. A `400` response naming `update_set_name` or `update_set_id` is treated as evidence that the API route is installed and reachable by the OAuth identity. `401`, `403`, and `404` fail closed.

This probe does not prove that generated XML can be imported directly. The CI/CD Update Set API is the preferred lifecycle surface for create/retrieve/preview/commit/backout operations, but retrieval still expects a ServiceNow update source and source update set identity. If generated implementation XML remains the handoff artifact, a reviewed ServiceNow-side importer or a separate build/source instance is still required before CI/CD preview and commit can become the production path.

`ServiceNowClient` exposes explicit CI/CD Update Set lifecycle methods for future orchestration:

- `retrieve_cicd_update_set()` calls `POST /api/sn_cicd/update_set/retrieve` with `update_set_id`, optional update source identity, `auto_preview`, and `cleanup_retrieved`.
- `preview_cicd_update_set()` calls `POST /api/sn_cicd/update_set/preview/{remote_update_set_id}`.
- `commit_cicd_update_set()` calls `POST /api/sn_cicd/update_set/commit/{remote_update_set_id}` with `force_commit=false` by default.
- `fetch_cicd_progress()` calls `GET /api/sn_cicd/progress/{progress_id}`.

These methods are not wired into automated fulfillment yet. Commit remains intentionally unreachable from runtime story processing until the promotion source, preview review, and approval gates are designed.

## Update Set XML Importer Bootstrap

The native retrieved update set XML import surface is the `sys_remote_update_set` UI action `Import Update Set from XML`, which opens `upload.do` with `sysparm_target=sys_remote_update_set`. That route is UI/session oriented and should not be automated from the sidecar with browser cookies or CSRF scraping.

Use `plan-update-set-importer` to generate a reviewed ServiceNow Scripted REST bootstrap spec instead:

```bash
python3 -m jedi_devproject.cli plan-update-set-importer \
  --integration-identity jedi-devproject-update-set-importer \
  --run-id update-set-importer-20260514-001 \
  --spec-root artifacts/update-set-importer
```

The spec creates a Scripted REST API definition with service id `jedi_update_set_import` and operation `import_update_set_xml`. ServiceNow generates the concrete `base_uri` for the instance namespace, for example `/api/<namespace>/jedi_update_set_import`; treat that value as discovered platform state rather than a portable spec field. The operation requires authentication and ACL authorization, accepts JSON, validates `update_set_xml`, and calls `GlideUpdateManager2().loadXML(xmlPayload)` server-side so ServiceNow imports the XML through platform update set mechanics.

After reviewing the generated spec, apply it with explicit confirmation:

```bash
python3 -m jedi_devproject.cli apply-update-set-importer \
  --env-file .env \
  --spec-file artifacts/update-set-importer/update-set-importer-20260514-001.json \
  --confirm-service-id jedi_update_set_import \
  --confirm-records \
  --audit-root artifacts/bootstrap-audit \
  --run-id update-set-importer-apply-20260514-001
```

Verify the installed Scripted REST records with:

```bash
python3 -m jedi_devproject.cli verify-update-set-importer \
  --env-file .env \
  --spec-file artifacts/update-set-importer/update-set-importer-20260514-001.json \
  --report-root artifacts/bootstrap-verification \
  --run-id update-set-importer-verify-20260514-001
```

This bootstrap only installs the importer endpoint. It does not send XML, preview, commit, or wire story fulfillment to promotion. Import smoke tests must use reviewed Update Set XML and should verify that `sys_remote_update_set` and related `sys_update_xml` rows appear before any CICD preview or commit operation is considered.

The PDI importer smoke on May 14, 2026 posted a minimal reviewed XML payload to the discovered endpoint `/api/1860704/jedi_update_set_import`. ServiceNow returned `201` with `status=imported` and created retrieved update set `JEDI XML Import Smoke 20260514 002` with sys_id `64c3e9d1b27a42479620114da017857a`, state `loaded`, and zero `sys_update_xml` rows. This proves the server-side XML import bridge works for retrieved update set headers; the next smoke must include real customer update rows.

The follow-on PDI smoke posted XML containing one `sys_remote_update_set` header plus two `sys_update_xml` customer update rows for a disposable field `u_jedi_import_smoke_notes`. ServiceNow created retrieved update set `JEDI XML Import Customer Updates Smoke 20260514 001` with sys_id `22221e3514c94fa3bde48148b0053e6f`, state `loaded`, and two remote customer updates: `sys_dictionary_rm_story_u_jedi_import_smoke_notes` and `sys_documentation_rm_story_u_jedi_import_smoke_notes_en`. Both rows were linked through `remote_update_set`; neither had a local `update_set`.

The CI/CD preview smoke for that retrieved update set succeeded. `preview_cicd_update_set()` returned progress id `d240c02ec330c710913fbf12b4013170`; progress completed with `status_label=Successful`, `percent_complete=100`, `has_preview_problem=false`, and `remote_update_set_id=22221e3514c94fa3bde48148b0053e6f`. The retrieved update set state became `previewed`, and `sys_update_preview_problem` returned zero rows. No commit was run.

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

For hosted runtime, the worker process should run `python -m jedi_devproject.runtime_worker` from `Dockerfile.worker`. The worker loop is controlled by:

- `JEDI_WORKER_MAX_ITERATIONS`: optional bounded loop count for smoke tests.
- `JEDI_WORKER_IDLE_SLEEP_SECONDS`: idle poll sleep interval. Defaults to `5.0`.
- `JEDI_WORKER_STOP_ON_FAILURE`: whether the process exits after the first failed job. Defaults to `false` for long-running workers.

Railway development now uses `JEDI_BUILD_CLAIM_APPLY=true` so live fulfillment moves the story to `Work in Progress` before model candidate generation. Keep the worker as a separate service from the public API service.

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

Recommended field:

- `story_sys_id` for authoritative ServiceNow record lookup

For the MVP, only `event_type=story_state_changed`, `table=rm_story`, `previous_state=Draft`, and `current_state=Ready` plans evaluation. The sidecar plan is `evaluate_story` with a later claim target of `Work in Progress`. A `Ready for Testing` to `Complete` transition plans `close_story` and is treated as a UAT closeout signal only. The API closes the operational loop immediately by setting `u_ai_status=Complete`; it does not wait in or enqueue a worker. A `Ready for Testing` to `Ready` transition plans `rework_requested`; it means the candidate was rejected but the story remains valid for rework. A `Ready for Testing` to `Draft` transition plans `story_rejected`; it means the story itself was rejected or reset. That claim must still perform a fresh ServiceNow story read and allowlisted state-transition check before any mutation.

The lifecycle event should include `story_sys_id` when emitted by ServiceNow. Story number is not guaranteed to be unique in every development or restored instance, so workers use `story_sys_id` as the authoritative lookup key when present and fall back to story number only for legacy events. Admin responses and public summaries still use story number and correlation ids; they do not need to expose ServiceNow internal record ids.

Bootstrap should eventually install or document the ServiceNow-side pieces needed for this contract: a Business Rule or Flow that detects `Draft` to `Ready`, a Scripted REST API or outbound REST Message path for event delivery, and the integration identity used in `emitted_by`. That bootstrap work must be explicit and reviewed; this contract alone does not create ServiceNow scripts.

Business Rule first is the preferred lifecycle trigger bootstrap. A scoped after-update Business Rule on `rm_story` is deterministic, can inspect `previous` and `current` state, and is easier to review in an Update Set than a Flow. Flow remains a later option for approval composition, but the state-change emitter should stay small and table-local.

Use `plan-lifecycle-business-rule` to write a reviewable ServiceNow script artifact:

```bash
python3 -m jedi_devproject.cli plan-lifecycle-business-rule \
  --endpoint-url https://sidecar.example.gov/lifecycle/events \
  --integration-identity jedi-devproject-lifecycle-integration \
  --draft-state-value -6 \
  --ready-state-value 1 \
  --ready-for-testing-state-value -7 \
  --complete-state-value 3 \
  --hmac-secret-property-name x_jedi.lifecycle.webhook.secret \
  --run-id lifecycle-business-rule-20260513-001 \
  --spec-root artifacts/lifecycle-bootstrap
```

The command writes a local lifecycle webhook bootstrap bundle with two reviewed sections:

- `rest_message`: an Outbound REST Message named `Jedi DevProject Lifecycle Event API` with method `post_event`, HTTPS endpoint, JSON content type, and authentication marked `configured_in_servicenow`.
- `business_rule`: the `rm_story` after-update Business Rule script and condition.

When `--hmac-secret-property-name` is supplied, the generated Business Rule reads the signing secret from that ServiceNow system property, signs `<timestamp>.<body>` with `GlideCertificateEncryption.generateMac()`, and sends `X-JEDI-Webhook-Timestamp` plus `X-JEDI-Webhook-Signature: sha256-base64=<mac>`. The bootstrap artifact records only the property name, not the secret value. Operators must create or update the ServiceNow property value out of band and set the same secret in the API runtime as `JEDI_LIFECYCLE_WEBHOOK_SECRET`.

The Business Rule references the named REST Message instead of setting the endpoint directly. This keeps the endpoint URL out of the Business Rule script, lets ServiceNow own authentication configuration, and gives reviewers a clean separation between trigger logic and transport configuration.

The generated Business Rule emits `story_state_changed` when the state changes from the supplied Draft value to the supplied Ready value. If `--ready-for-testing-state-value` and `--complete-state-value` are supplied, it also emits Ready for Testing transitions to Complete, Ready, and Draft. The generated payload includes story number, `story_sys_id`, and correlation ids; the sidecar uses `story_sys_id` for worker lookup and story number for human-readable correlation. This command does not install the Business Rule, create a Flow, or mutate ServiceNow.

The artifact also includes `servicenow_records`, a deterministic plan for the ServiceNow tables that later apply code must create or update:

- `sys_rest_message`
- `sys_rest_message_fn`
- `sys_script`

Each record includes an `insert_or_update` operation, lookup keys, and the fields to write. The planning command does not apply those records. Live apply must use this record plan, require explicit confirmation, and write audit evidence before making ServiceNow changes.

The bootstrap writes the public endpoint to ServiceNow's `rest_endpoint` fields and resolves the REST method's `rest_message` parent by the installed REST Message `sys_id`. Verification normalizes ServiceNow boolean strings and reference field `{value, link}` responses before comparing the installed records with the reviewed spec. The current PDI bootstrap can continue using `no_authentication` only when the API runtime is in `development` with lifecycle webhook auth disabled. Before any non-PDI use, configure the ServiceNow emitter to send the `hmac_sha256` headers described in Lifecycle Webhook Authentication, or replace it with the approved OAuth-backed mode after that path is implemented.

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

The bootstrap plan only covers automation metadata fields on `rm_story`:

- `u_ai_status`
- `u_ai_handoff_type`
- `u_ai_handoff_reference`
- `u_ai_artifact_reference`

`u_ai_build_reference` and `u_ai_candidate_artifact` are legacy external-build fields. Existing instances may keep them for historical records, but the retrieved Update Set handoff path no longer requires them.

These fields are dictionary-writable by design because the worker must update them through the ServiceNow Table API. If an operational field already exists with dictionary `read_only=true`, the apply command patches the `sys_dictionary` record back to `read_only=false`. Do not use dictionary read-only as the operator protection boundary for these fields.

`apply-bootstrap-fields` also installs the `Jedi DevProject read-only automation metadata` UI Policy on `rm_story`. The policy runs on load and calls `g_form.setReadOnly(...)` for each automation metadata field, making the fields read-only in the ServiceNow form experience while preserving the Table API write path for the integration identity. The bootstrap does not create `state`, and it does not place these fields on the Story form. Project teams can decide later whether these operational fields should be visible on the Story form.

Use `apply-bootstrap-fields` to create the missing custom table fields after reviewing the plan:

```bash
python3 -m jedi_devproject.cli apply-bootstrap-fields \
  --env-file .env \
  --confirm-table rm_story \
  --confirm-fields \
  --audit-root artifacts/bootstrap-audit \
  --run-id bootstrap-fields-20260513-001
```

The apply command requires both `--confirm-table rm_story` and `--confirm-fields`. It creates only the missing custom fields, applies the metadata read-only UI Policy, and writes a bootstrap audit artifact. It makes no form layout changes and does not create `state`.

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

The contract rejects unknown fields, including ServiceNow `story_sys_id`. The external build contract is downstream of lifecycle intake and should use story number and artifact references rather than internal ServiceNow record ids.

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
