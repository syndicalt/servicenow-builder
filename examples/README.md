# CLI Cookbook

Runnable recipes for the `jedi-devproject` CLI. Install first with
`pip install -e '.[dev]'` (see `docs/quickstart.md`).

## Conventions

- **Dry-run by default.** No command mutates ServiceNow unless you pass an explicit
  `--apply` flag plus the matching confirmation argument (for example
  `--confirm-story-number`).
- **Summary-line output.** Commands print one `key=value` summary line to stdout and
  return exit code `0` on success, `1` on a blocked or failed outcome.
- **Write-once artifacts.** Artifact files are never overwritten. Re-running a command
  with the same `--run-id` fails with `ArtifactWriteError: artifact already exists`.
  Use a fresh run ID per run.
- **Redacted diagnostics.** Error output uses stable reason codes and never echoes
  credential-like values, local paths inside reason codes, or payload fragments.
- Commands that need ServiceNow or PostgreSQL read `.env` by default; override with
  `--env-file`. See `docs/quickstart.md` step 2 for the required settings.

## Fixtures

`examples/stories/content-only-help-text.json` is a synthetic `rm_story` record for the
happy-path flow: a 2-point, content-only portal help-text change affecting `sp_instance`.
It contains no customer data or credentials.

Several recipes need small JSON input files. Create them once and reuse:

`provider-response.json` — a static provider response standing in for an approved model
call (changes must stay on the allowlisted tables and operations):

```json
{
  "changes": [
    {
      "table": "sp_instance",
      "operation": "update",
      "fields": {"description": "Send your request after confirming all required fields are complete."}
    }
  ],
  "test_plan": ["Confirm the portal help text matches the approved wording."],
  "rollback_notes": ["Restore the prior portal help text from the previous update set."]
}
```

`lifecycle-event.json` — a `Draft` → `Ready` state-change event as emitted by the
ServiceNow-side Business Rule:

```json
{
  "event_id": "EVT-EXAMPLE-001",
  "event_type": "story_state_changed",
  "source": "servicenow",
  "table": "rm_story",
  "story_number": "STORY-EXAMPLE-001",
  "story_sys_id": "example-story-001",
  "previous_state": "Draft",
  "current_state": "Ready",
  "occurred_at": "2026-08-10T00:00:00Z",
  "correlation_id": "CORR-EXAMPLE-001",
  "emitted_by": "lifecycle-business-rule"
}
```

`build-result.json` — an external build pipeline result contract. Successful builds must
reference reviewed delivery outputs:

```json
{
  "story_number": "STORY-EXAMPLE-001",
  "build_reference": "BUILD-2026-001",
  "status": "succeeded",
  "candidate_artifact_path": "artifacts/first-run/STORY-EXAMPLE-001.json",
  "reviewed_update_set_xml_path": "artifacts/exports/reviewed-smoke/STORY-EXAMPLE-001.xml",
  "test_evidence_path": "artifacts/exports/reviewed-smoke/STORY-EXAMPLE-001.xml",
  "build_actor_id": "builder.example",
  "failure_reasons": [],
  "message": null
}
```

## 1. Local Pipeline — No Credentials Needed

### Run the candidate pipeline on a sample story

```bash
jedi-devproject run-local \
  --sample-file examples/stories/content-only-help-text.json \
  --artifact-root artifacts \
  --run-id first-run
```

```text
run_id=first-run stories_processed=1 eligible=1 manual_review=0 rejected=0 generated_candidates=1 artifact_count=1 enriched_stories=0 enrichment_manual_review=0 inferred_tables=0 automated_development_candidates=1
```

Writes `artifacts/first-run/STORY-EXAMPLE-001.json` (the `UpdateSetCandidate`).

### Build a model-ready implementation packet

```bash
jedi-devproject build-implementation-packet \
  --sample-file examples/stories/content-only-help-text.json \
  --artifact-root artifacts/implementation-packets \
  --run-id packet-run
```

```text
implementation_packets=1 run_id=packet-run
```

Writes `artifacts/implementation-packets/packet-run/STORY-EXAMPLE-001.json`: the
citation-backed context bundle sent to an approved provider. Use `--story-number`
instead of `--sample-file` to fetch the story from a live instance.

### Build a validated candidate from a static provider response

```bash
jedi-devproject build-implementation-candidate \
  --sample-file examples/stories/content-only-help-text.json \
  --provider-response-file provider-response.json \
  --artifact-root artifacts/implementation-candidates \
  --run-id candidate-run
```

```text
implementation_candidates=1 run_id=candidate-run
```

The response is validated against the table/operation allowlist and sys_id policy before
the candidate artifact is written.

### Run a batch of candidate jobs

`jobs.json`:

```json
[
  {
    "sample_file": "examples/stories/content-only-help-text.json",
    "provider_response_file": "provider-response.json"
  }
]
```

```bash
jedi-devproject run-implementation-candidates \
  --jobs-file jobs.json \
  --artifact-root artifacts/implementation-candidates \
  --batch-report-root artifacts/implementation-candidate-batches \
  --run-id batch-run
```

```text
total=1 built=1 blocked=0
```

Writes a batch report to `artifacts/implementation-candidate-batches/batch-run.json`.
Exit code is `1` when any job is `blocked`.

## 2. Lifecycle and External Build Planning — Local

### Plan orchestration from a lifecycle event

```bash
jedi-devproject process-lifecycle-event \
  --event-file lifecycle-event.json \
  --run-id event-plan \
  --plan-root artifacts/lifecycle-plans
```

```text
lifecycle_event_plans=1 story_number=STORY-EXAMPLE-001 should_evaluate=True claim_state=Work in Progress path=artifacts/lifecycle-plans/event-plan.json
```

Only `story_state_changed` events on `rm_story` transitioning `Draft` → `Ready` produce
`should_evaluate=True`; anything else is planned as a no-op with reasons.

### Plan downstream jobs from an external build result

```bash
jedi-devproject process-external-build-result \
  --result-file build-result.json \
  --from-state "Work in Progress" \
  --run-id build-result-run \
  --writeback-job-root artifacts/writeback-jobs \
  --delivery-job-root artifacts/delivery-jobs
```

```text
external_build_results=1 writeback_jobs=1 reviewed_delivery_jobs=2 writeback_job_file=artifacts/writeback-jobs/build-result-run.json delivery_job_file=artifacts/delivery-jobs/build-result-run.json
```

Failed or blocked build results (`"status": "failed"` / `"blocked"`, with
`failure_reasons` or `message` required) produce a writeback job but no delivery jobs.

## 3. Delivery Artifacts — Local Smoke Flow

### Create a placeholder delivery artifact (not attachable)

```bash
jedi-devproject run-delivery-artifact-smoke \
  --run-id delivery-smoke \
  --story-number STORY-EXAMPLE-001 \
  --artifact-root artifacts
```

```text
delivery_artifact_created=True delivery_attachments_planned=0 delivery_attachments_applied=0
```

The placeholder uses the `smoke_placeholder` delivery contract, so the handoff report
classifies it as internal evidence (`attach_to_servicenow=false`). This exercises the
attachment gate without producing anything attachable.

### Create a reviewed delivery artifact (attachable)

```bash
jedi-devproject run-reviewed-delivery-smoke \
  --run-id reviewed-smoke \
  --story-number STORY-EXAMPLE-001 \
  --reviewer-id reviewer.example \
  --artifact-root artifacts
```

```text
reviewed_delivery_artifacts=1 handoff_plans=1 delivery_attachments_planned=1 delivery_attachments_applied=0 lifecycle_manifest_written=True
```

The `reviewed_export` contract plus a named `--reviewer-id` is what makes an artifact
eligible for attachment. Writes the export XML, a reviewed delivery job, an artifact
handoff report, and a lifecycle manifest under `artifacts/`.

### Record a reviewer decision on an existing artifact

```bash
jedi-devproject review-delivery-artifact \
  --run-id review-run \
  --story-number STORY-EXAMPLE-001 \
  --artifact-kind update_set_xml \
  --artifact-path artifacts/exports/reviewed-smoke/STORY-EXAMPLE-001.xml \
  --reviewer-id reviewer.example \
  --job-root artifacts/reviewed-delivery-jobs
```

```text
reviewed_delivery_artifacts=1 story_number=STORY-EXAMPLE-001 path=artifacts/reviewed-delivery-jobs/review-run.json
```

`--artifact-kind` accepts `update_set_xml` or `test_evidence_bundle`.

### Plan an artifact handoff from a jobs file

```bash
jedi-devproject plan-artifact-handoff \
  --run-id handoff-run \
  --story-number STORY-EXAMPLE-001 \
  --jobs-file artifacts/reviewed-delivery-jobs/review-run.json \
  --report-root artifacts/artifact-handoff-reports
```

```text
handoff_plans=1 total=1 attach_to_servicenow=1 internal_evidence=0 delivery_evidence=1
```

The jobs file is a JSON list of
`{"artifact_kind", "artifact_path", "approved_for_delivery", "delivery_contract"?}`
entries. Only approved artifacts with the `reviewed_export` contract plan an attachment.

### Preview attachment and work-note writeback (dry-run)

```bash
jedi-devproject attach-delivery-artifacts \
  --report-file artifacts/artifact-handoff-reports/handoff-run.json
```

```text
delivery_attachments_planned=1 delivery_attachments_applied=0 dry_run=True
```

```bash
jedi-devproject write-artifact-handoff-summary \
  --report-file artifacts/artifact-handoff-reports/handoff-run.json
```

```text
handoff_summary_written=False story_number=STORY-EXAMPLE-001 dry_run=True
```

Both verify the artifact SHA-256 against the report before doing anything. Applying
requires `--apply --confirm-story-number STORY-EXAMPLE-001 --actor-id <id>` (attachment
also requires `--audit-root` and `--run-id`) and a reachable instance.

## 4. Lifecycle Manifests — Local

Tie the phase artifacts of a run together:

```bash
jedi-devproject record-lifecycle-manifest \
  --run-id manifest-run \
  --story-number STORY-EXAMPLE-001 \
  --build-reference BUILD-2026-001 \
  --packet-path artifacts/implementation-packets/packet-run/STORY-EXAMPLE-001.json \
  --candidate-path artifacts/implementation-candidates/candidate-run/STORY-EXAMPLE-001.json \
  --manifest-root artifacts/lifecycle-manifests
```

```text
lifecycle_manifest_written=True story_number=STORY-EXAMPLE-001 path=artifacts/lifecycle-manifests/manifest-run.json
```

Add `--writeback-audit-path`, `--verification-verified`, and `--verification-state` after
a verified writeback to close the loop.

## 5. ServiceNow-Connected Commands

These need the PM/DEV OAuth credentials from `.env`. They are still dry-run unless an
apply path is explicitly confirmed.

### Fetch stories from an instance and run the pipeline

```bash
jedi-devproject run-pdi --run-id pdi-run --limit 5
jedi-devproject run-pdi --run-id pdi-run-2 --sysparm-query "state=Ready^points<=3"
jedi-devproject run-pdi --run-id pdi-run-3 --project-sys-id <project-sys-id>
```

Prints the same summary line as `run-local`.

### End-to-end lifecycle smoke (fetch → packet → candidate → writeback plan)

```bash
jedi-devproject run-lifecycle-smoke \
  --story-number STORY-EXAMPLE-001 \
  --provider-response-file provider-response.json \
  --build-reference BUILD-2026-001 \
  --from-state "Work in Progress" \
  --artifact-root artifacts \
  --run-id lifecycle-smoke
```

```text
packet_built=1 candidate_built=1 writeback_allowed=True writeback_applied=False
```

Always dry-run. Exit code is `1` when the writeback plan is not allowed.

### Check writeback capability

```bash
jedi-devproject check-writeback-capability
```

```text
allowed=True ready_for_testing_state=Ready for Testing missing_fields= reasons=
```

Discovers the `Ready for Testing` choice value from `sys_choice` and validates the
required structured fields on `rm_story` via `sys_dictionary`. Exits `1` when the
instance is not writeback-capable, with `missing_fields`/`reasons` populated.

### Check the CI/CD Update Set API

```bash
jedi-devproject check-cicd-update-set-capability
```

```text
available=True <probe>_status=200 ... reasons=
```

### Plan (or apply) a story writeback

```bash
jedi-devproject plan-writeback \
  --story-number STORY-EXAMPLE-001 \
  --build-reference BUILD-2026-001 \
  --from-state "Work in Progress" \
  --artifact-url artifacts/implementation-candidates/candidate-run/STORY-EXAMPLE-001.json
```

```text
dry_run=True story_number=STORY-EXAMPLE-001 allowed=True <field>=<value> ...
```

`--build-status` accepts `succeeded` (default), `failed`, or `blocked`; unsuccessful
builds never advance the story state. To apply, add `--apply --confirm-story-number
STORY-EXAMPLE-001 --actor-id <id>`; a second line `applied=True ...` confirms the
mutation. Apply paths write write-once audit artifacts and treat repeated runs as
idempotent no-ops.

### Verify a completed writeback

```bash
jedi-devproject verify-writeback \
  --story-number STORY-EXAMPLE-001 \
  --build-reference BUILD-2026-001
```

```text
verified=True story_number=STORY-EXAMPLE-001 expected_state=Ready for Testing <field>=<value> ...
```

### Run a writeback batch

`writeback-jobs.json` — a JSON list of job records
(`artifact_url` and `build_status` optional):

```json
[
  {
    "story_number": "STORY-EXAMPLE-001",
    "build_reference": "BUILD-2026-001",
    "artifact_url": "artifacts/implementation-candidates/candidate-run/STORY-EXAMPLE-001.json",
    "build_status": "succeeded",
    "from_state": "Work in Progress"
  }
]
```

```bash
jedi-devproject run-writeback-batch \
  --jobs-file writeback-jobs.json \
  --actor-id svc-jedi-writeback \
  --audit-root artifacts/audit/writeback \
  --batch-report-root artifacts/writeback-batch-reports \
  --execution-id batch-001
```

```text
total=1 allowed=1 applied=0 idempotent=0 blocked=0
```

Without `--apply` every job stays a plan. Exits `1` when any job is `blocked`.

## 6. ServiceNow Bootstrap

Plan reviewable specs locally; apply and verify against the instance.

### Business Rule spec for lifecycle events (local)

```bash
jedi-devproject plan-lifecycle-business-rule \
  --endpoint-url https://<sidecar-host>/lifecycle/events \
  --integration-identity jedi-lifecycle-svc \
  --draft-state-value Draft \
  --ready-state-value Ready \
  --ready-for-testing-state-value "Ready for Testing" \
  --complete-state-value Complete \
  --run-id br-spec \
  --spec-root artifacts/lifecycle-specs
```

```text
lifecycle_business_rule_specs=1 table=rm_story rest_message=Jedi DevProject Lifecycle Event API path=artifacts/lifecycle-specs/br-spec.json
```

### Update Set importer spec (local)

```bash
jedi-devproject plan-update-set-importer \
  --integration-identity jedi-importer-svc \
  --run-id importer-spec \
  --spec-root artifacts/importer-specs
```

```text
update_set_importer_specs=1 service_id=jedi_update_set_import path=artifacts/importer-specs/importer-spec.json
```

### Plan missing bootstrap fields (connected, read-only)

```bash
jedi-devproject plan-bootstrap-fields
```

```text
ready=False table=rm_story missing_fields=u_ai_status,... fields_to_create=N fields_to_update_writable=N form_layout_changes=N
```

Exits `0` when the instance already has every required field.

### Apply and verify (connected, confirmed mutation)

```bash
jedi-devproject apply-bootstrap-fields \
  --confirm-table rm_story --confirm-fields \
  --audit-root artifacts/audit/bootstrap --run-id bootstrap-001

jedi-devproject apply-lifecycle-webhook \
  --spec-file artifacts/lifecycle-specs/br-spec.json \
  --confirm-table rm_story --confirm-records \
  --audit-root artifacts/audit/lifecycle-webhook --run-id webhook-001

jedi-devproject verify-lifecycle-webhook \
  --spec-file artifacts/lifecycle-specs/br-spec.json \
  --report-root artifacts/lifecycle-webhook-verification --run-id webhook-verify-001

jedi-devproject apply-update-set-importer \
  --spec-file artifacts/importer-specs/importer-spec.json \
  --confirm-service-id jedi_update_set_import --confirm-records \
  --audit-root artifacts/audit/update-set-importer --run-id importer-001

jedi-devproject verify-update-set-importer \
  --spec-file artifacts/importer-specs/importer-spec.json \
  --report-root artifacts/update-set-importer-verification --run-id importer-verify-001
```

Apply commands refuse to run without both confirmation arguments and print
`applied=False` with a stable reason (`bootstrap_confirmation_required`,
`lifecycle_webhook_confirmation_required`, or
`update_set_importer_confirmation_required`), exiting `1`. Verify commands print
`..._verified=True matched_records=N missing_records=0 path=...` and exit `1` on any
mismatch.

## 7. Operational Store

```bash
jedi-devproject init-operational-store
```

```text
operational_store_schema_ready=true
```

Applies the bundled SQL migrations and verifies the required tables. Exit `1` with
`operational_store_schema_ready=false` when tables are missing. See
`docs/quickstart.md` step 5 for details and the known `verify_schema_ready()` defect.

## Common Failure Modes

| Output / error | Exit | Cause | Fix |
|---|---|---|---|
| `ArtifactWriteError: artifact already exists: ...` | 1 | Write-once artifact path already used. | New `--run-id` (or remove the stale artifact directory). |
| `RuntimeConfigError: Missing required runtime settings: ...` | 1 | `.env` missing keys the command needs. | Complete `.env`; the error lists the missing keys. |
| `json_input_invalid_json` / `json_input_invalid_utf8` / `json_input_too_large` | 1 | Malformed or oversized JSON input (10 MiB cap). | Validate the file with `python3 -m json.tool`. |
| `implementation_packets=0 reason=no_stories_found` | 1 | Story lookup returned nothing. | Check `--story-number` / `--sysparm-query` and instance connectivity. |
| `reason=story_lookup_result_unsafe` | 1 | The ServiceNow client returned an unexpected payload shape; the CLI refuses to process it. | Inspect instance response and client configuration. |
| `reason=confirmation_mismatch` | 1 | `--confirm-story-number` (or table/service confirmation) does not match the target. | Re-type the exact story number, table, or service ID. |
| `reason=actor_identity_required` | 1 | Apply path without `--actor-id`. | Pass `--actor-id` (service principal or human identity). |
| `reason=artifact_hash_mismatch` / `reason=artifact_missing` | 1 | Artifact changed or disappeared after the handoff report was written. | Regenerate the report from the current artifact. |
| `reason=attachment_audit_already_exists` | 1 | Attachment audit for this `--run-id` already exists (idempotency guard). | Treat as already applied, or use a new run ID. |
| `total=0 built=0 blocked=0 reason=no_jobs` | 1 | Empty jobs file. | Add at least one job entry. |
| `lifecycle_event_plans=0 reason=invalid_lifecycle_event ...` | 1 | Event JSON fails schema validation (`extra="forbid"`). | Remove unknown fields; check required keys. |
| `usage: jedi-devproject ... error: the following arguments are required` | 2 | Missing required CLI flag. | Re-run with `--help` for the exact signature. |
| `psycopg.errors.InvalidTextRepresentation: malformed array literal` | 1 | Known `verify_schema_ready()` defect against real PostgreSQL (see quickstart troubleshooting). | Code fix required; not a configuration problem. |

## Notes

- All fixture and recipe data is synthetic. Keep customer-specific URLs, story numbers,
  and credentials in `.env`, never in committed files.
- The full flag-level reference for every command is available via
  `jedi-devproject <command> --help`; the subcommand implementations live in
  `src/jedi_devproject/cli_pipeline.py`, `cli_writeback.py`, `cli_delivery.py`, and
  `cli_bootstrap.py`.
