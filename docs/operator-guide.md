# Operator Guide

For the full runtime architecture, workflow diagrams, and data-flow diagrams, see `docs/system-architecture.md`.

## Local Configuration

Create a local `.env` file using `.env.example` as the template:

```bash
SERVICENOW_INSTANCE_URL=https://<instance>.service-now.com
SERVICENOW_CLIENT_ID=...
SERVICENOW_CLIENT_SECRET=...
```

Local configuration examples use neutral ServiceNow placeholders. Replace
`https://<instance>.service-now.com` with the approved PM or development target before running local
tools, and keep customer-specific or PDI-specific URLs in `.env`, not `.env.example` or committed
operator documentation.

Never commit `.env`.

Docker build context excludes `.env*` so local credentials such as `.env`, `.env.local`, and
environment-specific overrides cannot be copied into API or worker images by later Dockerfile
changes. The `.dockerignore` contract keeps `!.env.example` available as non-secret configuration
documentation.

Docker build context also excludes local runtime evidence and test artifacts. `.eventloom/`,
`.coverage`, `coverage.xml`, virtual environments, tox workspaces, cache directories, and generated
artifact output stay outside image build context so local orchestration traces, coverage databases,
and development-only dependency state cannot be captured into a future image layer.

Docker build context excludes local control-plane configuration. `.mcp.json`, `zaxy-mcp.json`,
`.claude/`, `.codex/`, and common private-key or certificate bundle extensions such as `*.pem`,
`*.key`, `*.p12`, and `*.pfx` stay outside image build context, even though current Dockerfiles copy
only explicit package sources. This keeps future Dockerfile changes from accidentally capturing
operator-local connectors, agent settings, or credential material.

Local `.env` files are bounded before parsing. CLI, runtime API, and worker paths that load an env file reject files larger than 1 MiB with `dotenv_input_too_large` before credential parsing, runtime setting validation, or ServiceNow client creation. The `.env` loader also requires a regular file and rejects symlinked or non-regular paths with `dotenv_must_be_regular_file`, so local credential loading cannot silently follow filesystem indirection. Invalid UTF-8 bytes fail as `dotenv_invalid_utf8`. These size, regular-file, and decode diagnostics preserve stable reason codes without echoing raw env file paths or credential-like payload fragments.

ServiceNow dotenv read diagnostics do not retain unsafe causes. Symlinked or non-regular `.env`
paths fail with `dotenv_must_be_regular_file`, and invalid UTF-8 env files fail with
`dotenv_invalid_utf8`. Those public `ValueError` instances suppress the original
`ArtifactReadError` or `UnicodeDecodeError`, so crash reporters, traceback formatters, and operator
logs do not retain local env paths, path-derived credential fragments, raw env bytes, or env key names
in `__cause__`.

Local `.env` assignment keys are strict. The parser still ignores comments, blank lines,
and non-assignment lines, but assignment keys must be non-empty, unpadded, and free of
whitespace or control characters. Assignment keys must use shell-compatible uppercase
environment-variable syntax: start with a letter or underscore and contain only uppercase
letters, digits, and underscores. Duplicate assignment keys are rejected with
`dotenv_duplicate_key` instead of using last-value-wins behavior, so a local env file cannot
hide which ServiceNow target, credential, model provider, or runtime control value was
actually loaded.

Local `.env` value quote handling is strict. Matching single or double quotes around a
value are accepted and removed, but unmatched or mixed boundary quotes are rejected with
`dotenv_invalid_value_quotes` before credentials or runtime controls are returned. The
diagnostic names the assignment key and does not echo the configured value.

Project TOML configuration files are also bounded before parsing. The local project config loader rejects files larger than 1 MiB with `project_config_too_large` before TOML decoding or required-setting validation, and it rejects symlinked or non-regular config paths with `project_config_must_be_regular_file`. Invalid UTF-8 bytes fail as `project_config_invalid_utf8`. Required project config values are validated before `AppConfig` is returned: `servicenow_instance_url` must be an HTTPS ServiceNow URL without credentials, fragments, whitespace, encoded whitespace/control characters, or control characters; `artifact_dir` and `target_boundary` must be unpadded and free of control characters. Malformed project config diagnostics name the setting and do not echo URL credentials, configured value fragments, decoded payload fragments, or the raw config file path.

Project config read diagnostics do not retain unsafe causes. Symlinked or non-regular project TOML paths still fail with `project_config_must_be_regular_file`, and invalid UTF-8 still fails with `project_config_invalid_utf8`, but those public `ConfigError` values do not chain the underlying `ArtifactReadError` or `UnicodeDecodeError`. This keeps traceback, API, and CLI error serialization from re-exposing sensitive local paths, bytes, or decoded fragments through `__cause__`.

CLI validation error output is redacted before printing to stdout. Bootstrap and delivery commands that catch invalid JSON, invalid DTOs, or invalid artifact handoff inputs preserve stable reason codes such as `invalid_build_result`, `invalid_lifecycle_webhook_spec`, and `json_input_too_large`, but diagnostic details redact URL credentials, sensitive query parameters, Authorization header values, cookie values, private-key blocks, and sensitive assignment fragments such as `client_secret=...`. This protects operator terminals, CI logs, and copied support output even when a local input path or malformed value contains secret material.

CLI JSON artifact input parsing is strict. Shared local JSON loaders reject malformed JSON and
non-standard JSON numeric constants such as `NaN`, `Infinity`, and `-Infinity` with the stable
`json_input_invalid_json` reason code before DTO validation, provider-response validation, batch
handoff processing, or report generation. The diagnostic does not echo local file paths, submitted
field names, credential-like keys, or payload values.

CLI and worker JSON artifact output is strict as well. Shared write-once artifact serialization
uses strict JSON numeric handling and rejects payloads containing non-finite numeric values with
`artifact JSON payload contains non-finite numeric values` before opening the target artifact file.
The diagnostic does not echo artifact payload field names, credential-like keys, or values, and the
write-once path still preserves existing file, symlink, and path traversal protections.

Artifact JSON output diagnostics do not retain unsafe causes. Generic write-once JSON artifact
output still fails with `artifact JSON payload contains non-finite numeric values` when a corrupted
report or batch payload contains `NaN`, `Infinity`, or `-Infinity`, but the public
`ArtifactWriteError` does not chain the lower-level JSON encoder exception. Crash reporters,
traceback formatters, CLI output, and work-note writers therefore cannot re-expose artifact payload
field names, credential-like keys, JSON token fragments, or malformed values through `__cause__`.

Legacy Pydantic DTO artifact writers are strict JSON too. `_artifact_model_json()` preflights
candidate, writeback audit, and build-claim audit DTO payloads with strict JSON numeric handling
before write-once artifact output. If corrupted in-process DTOs contain `NaN`, `Infinity`, or
`-Infinity`, artifact writing fails with `artifact DTO payload contains non-finite numeric values`.
Unsupported non-JSON DTO payload values fail with `artifact DTO payload contains non-JSON values`.
DTO artifact writing does not call `str()` or `repr()` on unsupported objects, bytes, or custom
scalar values. DTO payload keys and text values must be exact strings; string subclasses fail with
the same non-JSON diagnostic before write-once artifact output. DTO payload traversal accepts only
exact dictionaries, lists, and tuples; dictionary, list, and tuple subclasses fail before `items()`,
iteration, or subclass hooks can execute. The diagnostic does not echo DTO field names. It also does
not echo story identifiers, audit values, or payload values, and the existing file, symlink, and path
traversal protections still apply.

Artifact DTO diagnostics do not retain unsafe causes. Candidate, writeback audit, and build-claim
DTO artifact writers still fail with `artifact DTO payload contains non-finite numeric values` or
`artifact DTO payload contains non-JSON values`, but those public `ArtifactWriteError` instances do
not chain lower-level Pydantic, validation, or JSON encoder exceptions. Crash reporters, traceback
formatters, CLI output, and work-note writers therefore cannot re-expose DTO field names, story
identifiers, audit values, credential-like fragments, object type names, or malformed values through
`__cause__`.

Shared artifact hash generation is strict JSON too. `stable_artifact_hash()` hashes a canonical
strict-JSON representation and rejects non-finite numeric values with
`artifact hash payload contains non-finite numeric values` before SHA-256 computation. The
diagnostic does not echo payload field names, credential-like keys, or values, so provenance hashes
cannot be minted over Python-only `NaN`, `Infinity`, or `-Infinity` tokens. Unsupported non-JSON
payload values are also rejected with `artifact hash payload contains non-JSON values`; artifact
hashing does not call `str()` or `repr()` on unsupported objects, bytes, or custom scalar values.
Artifact hash payload keys and text values must be exact strings; string subclasses fail with the
same non-JSON diagnostic before canonicalization or SHA-256 computation.
Artifact hash boolean and integer values must be exact JSON scalar types as well; boolean and integer
subclasses fail with the same non-JSON diagnostic before canonicalization or SHA-256 computation.
Artifact hash traversal accepts only exact dictionaries and lists; dictionary and list subclasses
fail before `items()`, iteration, canonicalization, or SHA-256 computation can execute subclass
hooks.

Stable artifact hash diagnostics do not retain unsafe causes. Non-finite payloads still fail with
`artifact hash payload contains non-finite numeric values`, and unsupported payload structures still
fail with `artifact hash payload contains non-JSON values`, but those public `ValueError` instances
do not chain the lower-level validation or JSON encoder exceptions. This keeps provenance,
traceback, and artifact-report serialization from re-exposing payload field names, object type
names, credential-like keys, or malformed values through `__cause__`.

CLI implementation-candidate batch blocked reasons are also stringification-safe. If an offline candidate job raises a malformed exception while the batch runner records a blocked outcome, the batch report stores `CLI batch raised unstringifiable <ExceptionType>` or `CLI batch raised unstringifiable exception` instead of letting a secondary exception prevent the JSON report artifact from being written.

CLI exception rendering uses the shared safe exception diagnostic helper before redaction. If an
exception raised during CLI handling cannot be stringified, the CLI prints a bounded
`CLI raised unstringifiable <ExceptionType>` diagnostic, or `CLI raised unstringifiable exception`
when the type label is unsafe, instead of allowing a secondary stringification failure to reach the
terminal or CI log.

OpenAI provider runtime validation diagnostics are exact-field only. When malformed provider
settings fail Pydantic validation, the runtime maps only exact validation locations for `api_key`,
`model`, and `base_url` to `OPENAI_API_KEY`, `OPENAI_MODEL`, and `OPENAI_BASE_URL`. Unknown,
non-string, string-subclass, or unstringifiable validation locations collapse to
`OPENAI_PROVIDER_SETTINGS`, so malformed validation metadata cannot execute custom `__str__` hooks
or leak provider setting fragments while the worker wraps startup configuration errors.

CLI summary output is sanitized before printing. Shared `render_summary()` output treats summary keys and values as untrusted report data: values are redacted, whitespace/control characters are collapsed, and each key or value is capped at 500 characters including the truncation marker before terminal output is produced.

Artifact handoff work-note summaries are also stringification-safe. The handoff work-note planner
formats only exact strings, booleans, integers, finite floats, and null summary values before passing
them through the shared work-note sanitizer. Unsupported summary values render as
`[unsupported handoff summary value]`, so malformed handoff report dictionaries cannot execute
custom `__str__` methods before redaction and truncation.

Artifact handoff delivery job extraction is fail-closed. `delivery_attachment_jobs_from_report()`
accepts only exact string story numbers and exact string attachment fields, requires the `decisions`
collection to be a list of dictionaries, and requires `attach_to_servicenow` to be an actual boolean
before deciding whether to create a ServiceNow attachment job. Malformed report shapes or unsupported
Python values fail with `artifact_handoff_report_invalid` without calling custom `__str__` or
`__bool__` methods. Valid attachable decisions still require the reviewed export contract and an
artifact hash before delivery.

Artifact handoff report creation uses the same malformed-report boundary. `build_artifact_handoff_report()`
validates exact string run ids, story numbers, artifact kinds, artifact paths, and optional delivery
contracts, requires artifact inputs to be dictionaries, and requires `approved_for_delivery` to be an
actual boolean before artifact planning or SHA-256 hashing begins. Unsupported Python values fail
with `artifact_handoff_report_invalid` before path construction, enum parsing, or approval checks can
call custom string or truthiness hooks.

Admin artifact payload views sanitize dictionary keys as well as values before rendering JSON or HTML diagnostics. Persisted artifact payload keys are treated as untrusted report data: secret-like assignment fragments are redacted, whitespace/control characters are collapsed, and each key is capped at 500 characters including the truncation marker. If a payload key sanitizes to an empty label, the diagnostic view renders it as `[empty key]`. Non-string payload keys render as `[non-string key]` instead of reflecting Python object representations or container contents. String-subclass payload keys also render as `[non-string key]` instead of reflecting subclass behavior. Non-string payload keys and string-subclass payload keys therefore share the same malformed-key label. Non-string keys are not stringified for sensitive-key classification, and string-subclass keys are not sent through work-note redaction, so malformed key objects cannot crash artifact diagnostics or surface exception text. If two payload keys collapse to the same sanitized label, the later labels receive a deterministic duplicate suffix instead of silently overwriting diagnostic content; the duplicate suffix is included inside the same 500-character bound.

Admin artifact payload scalar values are normalized to JSON-safe diagnostics before serialization. Exact strings are redacted and bounded, exact JSON primitives are preserved, non-finite floats render as `[non-json value]`, and unsupported scalar types such as bytes or Python objects also render as `[non-json value]` instead of reflecting raw bytes, object representations, or custom serializer errors. Admin artifact payload string, boolean, and integer values must be exact JSON scalar types; string, boolean, and integer subclasses render as `[non-json value]` before artifact API serialization or HTML rendering.

Admin artifact payload diagnostic JSON rendering is strict. `_admin_artifact_payload_json()` serializes redacted artifact payload views with strict JSON numeric handling before HTML rendering or truncation-preview generation. If a future projection defect or corrupted diagnostic view contains `NaN`, `Infinity`, or `-Infinity`, rendering fails with `admin artifact payload diagnostic contains non-finite numeric values`. The diagnostic does not echo payload field names, secret-bearing feedback, story identifiers, or payload values.

Admin artifact payload diagnostics do not retain unsafe causes. Malformed admin diagnostic payloads
still fail with `admin artifact payload diagnostic contains non-finite numeric values`, but the
public `ValueError` does not chain the lower-level JSON encoder exception. Crash reporters,
traceback formatters, admin HTML rendering, and API error serialization therefore cannot re-expose
payload field names, secret-bearing feedback, story identifiers, JSON token fragments, or malformed
values through `__cause__`.

Admin artifact payload traversal is cycle-safe. If an alternate store, migration defect, or corrupted fixture supplies a cyclic exact dictionary, exact list, or exact tuple, the diagnostic projection renders the repeated container as `[circular reference]` and marks the payload view as truncated instead of recursing until failure. Admin artifact payload views traverse only exact containers; dictionary, list, and tuple subclasses render as `[non-json value]` before `items()`, `len()`, iteration, or subclass hooks can execute.

Admin artifact payload traversal is also depth-bounded. Nested exact dictionaries, exact lists, and exact tuples are projected only to the configured diagnostic depth cap; deeper containers render as `[max depth exceeded]` and mark the payload view as truncated. This keeps operator diagnostics responsive when malformed artifacts contain extreme but acyclic nesting.

When a wide artifact payload is truncated, the internal `__jedi_payload_truncated__` diagnostic marker is inserted through the same collision-aware key renderer as user payload keys. If the original payload already contains that key, the user value remains visible and the internal marker receives a deterministic duplicate suffix.

Runtime response correlation never reflects arbitrary inbound request IDs. `X-Request-ID` is preserved only when it is 1 to 128 ASCII characters and contains letters, digits, hyphen, underscore, or period. Values with non-ASCII characters, whitespace, separators, control characters, oversized content, or secret-like assignment fragments are replaced with a generated UUID before `X-JEDI-Request-ID` is returned.

Runtime config numeric diagnostics do not retain unsafe causes. Integer and floating-point runtime setting parsers still fail closed with fixed, redacted diagnostics such as `runtime config raised unstringifiable UnstringifiableNumericRuntimeConfigError`, but the public `RuntimeConfigError` does not chain the lower-level parser exception. Crash reporters, traceback formatters, runtime startup logs, and API error serialization therefore cannot re-expose setting fragments, parser payloads, hostile exception text, or credential-like values through `__cause__`.

Runtime OpenAI provider setting diagnostics do not retain unsafe causes. `OPENAI_API_KEY` and `OPENAI_MODEL` env parsing still validates through the shared provider setting guards, but unstringifiable provider validation failures are wrapped as fixed `RuntimeConfigError` diagnostics such as `OPENAI_API_KEY provider setting raised unstringifiable UnstringifiableOpenAIProviderSettingError`. The public error does not chain the lower-level provider validation exception. Startup logs, worker failure notes, API error serialization, and crash reporters therefore cannot re-expose configured provider values, hostile exception text, or credential-like fragments through stringification or `__cause__`.

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

## Operational Store

The runtime uses PostgreSQL for durable operational state and DB-backed JSON artifacts. PostgreSQL is the MVP store for lifecycle orchestration because the API and worker runtime need production-shaped transactions, foreign keys, JSONB event payloads, row-level worker claims, and durable artifact records from the start.

The operational schema is defined in `db/migrations/0001_operational_store.sql` and initialized by `connect_operational_store(database_url=...)` in `jedi_devproject.operational_store`. It includes:

- `lifecycle_events`: inbound ServiceNow lifecycle events and their preserved original payload.
- `fulfillment_jobs`: one idempotent fulfillment job per lifecycle event, including status, attempt count, and worker lock metadata.
- `job_events`: append-only status history for queued, running, completed, blocked, or failed job transitions.
- `artifact_blobs`: durable JSON artifacts such as implementation packets and implementation candidates, stored with schema version, SHA-256 hash, story number, and job id.
- `artifact_refs`: stable artifact references with SHA-256 hashes. DB-backed artifacts use `db://artifact_blobs/<id>` paths and keep the `artifact_id` relation populated.

Operational-store JSON artifact blobs are strict JSONB evidence. `record_json_artifact()` serializes
the canonical payload used for both `payload_json` persistence and SHA-256 provenance with strict
JSON numeric handling. Payloads containing non-finite numeric values fail with
`operational artifact JSON payload contains non-finite numeric values` before hash computation,
transaction start, `artifact_blobs` insert, or `artifact_refs` insert. The diagnostic does not echo
payload field names, credential-like keys, or values. Unsupported non-JSON payload values fail with
`operational artifact JSON payload contains non-JSON values` before hash computation or transaction
start; DB-backed artifact persistence does not call `str()` or `repr()` on unsupported objects,
bytes, or custom scalar values. Operational artifact payload keys and text values must be exact
strings; string subclasses fail with the same non-JSON diagnostic before hash computation or
transaction start. Operational artifact payload traversal accepts only exact dictionaries, lists, and
tuples; dictionary, list, and tuple subclasses fail before `items()`, iteration, hash computation, or
transaction start.

Operational-store lifecycle event payloads are strict JSONB evidence too.
`record_lifecycle_event()` validates the Python-mode event payload, then serializes the event through
Pydantic JSON-mode output with strict JSON numeric handling before transaction start, event insert,
or idempotency lookup. If a corrupted in-process lifecycle event object contains `NaN`, `Infinity`,
or `-Infinity`, persistence fails with
`operational lifecycle event payload contains non-finite numeric values`. The diagnostic does not
echo event field names, ServiceNow sys_ids, correlation ids, or values. Unsupported non-JSON
payload values fail with `operational lifecycle event payload contains non-JSON values`; lifecycle
event persistence does not call `str()` or `repr()` on unsupported objects, bytes, or custom scalar
values. Lifecycle event payload keys and text values must be exact strings; string subclasses fail
with the same non-JSON diagnostic before transaction start or idempotency lookup. Lifecycle event
payload traversal accepts only exact dictionaries, lists, and tuples; dictionary, list, and tuple
subclasses fail before `items()`, iteration, transaction start, or idempotency lookup. Pydantic serializer warnings are suppressed so malformed payload shape is not leaked to logs.

Operational store JSONB diagnostics do not retain unsafe causes. Operational artifact and lifecycle
event payloads still fail with
`operational artifact JSON payload contains non-finite numeric values`,
`operational artifact JSON payload contains non-JSON values`,
`operational lifecycle event payload contains non-finite numeric values`, or
`operational lifecycle event payload contains non-JSON values`, but those public `ValueError`
instances do not chain lower-level Pydantic, validation, or JSON encoder exceptions. Crash reporters,
traceback formatters, work-note writers, and operational logs therefore cannot re-expose rejected
payload field names, ServiceNow sys_ids, correlation ids, credential-like keys, object type names, or
malformed values through `__cause__`.

Direct lifecycle and operational-store record validation suppresses rejected input values in Pydantic validation errors. Lifecycle ingress, lifecycle-event records, fulfillment jobs, job events, artifact refs, artifact blobs, retention reports, and surface maturity records still name invalid fields, but type, parsing, and validator failures do not echo rejected lifecycle payload fragments, ServiceNow sys_ids, job error text, artifact paths, artifact payload snippets, or retention setting fragments into logs, artifacts, or ServiceNow work notes.

The current claim primitive is `claim_next_fulfillment_job(worker_id=...)`. It uses `SELECT ... FOR UPDATE SKIP LOCKED` inside a PostgreSQL transaction to select the oldest queued job, mark it `running`, increment the attempt count, and set `locked_by` and `locked_at`. API and worker processes should use this store instead of treating JSON files as a queue.

### Operational Store Retention

Retention for the operational store is disabled by default and no record is ever deleted unless an explicit retention window is configured. This is intentional for a regulated deployment: prompts, outputs, and review evidence must follow agency/customer retention rules, and deleting operational evidence without an explicit customer policy is worse than storage growth. Enabling retention is therefore an explicit operator decision that must match the customer's approved retention schedule.

Configure retention through the worker environment:

```text
JEDI_RETENTION_ARTIFACT_BLOB_DAYS=<days, unset means never prune artifact_blobs>
JEDI_RETENTION_JOB_EVENT_DAYS=<days, unset means never prune job_events>
JEDI_RETENTION_PRUNE_BATCH_SIZE=500  # maximum 5000
JEDI_RETENTION_PRUNE_INTERVAL_SECONDS=3600  # maximum 86400
```

Both `*_DAYS` values are unset by default, which disables retention entirely. Each record class is pruned only when its own window is set, so an operator can prune heavy `artifact_blobs` payloads while keeping the full `job_events` history, or vice versa. Windows must be at least 1 day. `JEDI_RETENTION_PRUNE_BATCH_SIZE<=5000`, so maintenance cannot create unbounded lock or write bursts. Retention numeric values must parse as ASCII base-10 digits only without signs, underscores, padding, or control characters; empty values remain disabled, but whitespace-only or padded values fail retention policy loading with the setting name instead of being silently normalized.

What is pruned by `PostgresOperationalStore.prune_expired_records(policy=...)`:

- `artifact_blobs` rows older than `JEDI_RETENTION_ARTIFACT_BLOB_DAYS` whose fulfillment job is terminal (`completed`, `failed`, or `rejected`) and whose job has not been updated inside the window. The matching `artifact_refs` audit rows are kept with `artifact_id` detached; the `db://artifact_blobs/<id>` path and SHA-256 hash remain as durable provenance for the deleted payload.
- `job_events` rows older than `JEDI_RETENTION_JOB_EVENT_DAYS` for terminal jobs, under the same job-recency guard.

What is never pruned:

- `lifecycle_events`, `fulfillment_jobs`, `artifact_refs`, and `retention_prune_audit` rows. The lifecycle event, job record, and artifact reference chain stays intact so the audit correlation path is never orphaned.
- Any record attached to a `queued` or `running` job, regardless of age. In-flight work and its evidence always survive a prune.
- Anything at all when retention is disabled; a disabled policy performs zero queries.

Pruning is audit-safe and lock-friendly. Deletes run in bounded batches (`JEDI_RETENTION_PRUNE_BATCH_SIZE`, default 500 rows), each batch in its own short transaction, so a prune never holds long locks against the webhook or worker paths. Every prune returns a structured `RetentionPruneReport` with the cutoff, deleted count, and batch count per record class, and every run that deletes rows writes matching `retention_prune_audit` rows in PostgreSQL. Re-running a prune deletes nothing new, so the operation is idempotent. The supporting schema (`retention_prune_audit` plus `created_at` prune indexes) is defined in `db/migrations/0002_retention.sql` and applied automatically by `connect_operational_store(database_url=...)`.

Retention prune report hydration is exact-shape guarded before audit output. `RetentionClassPruneResult` requires exact string record classes, exact datetimes, exact non-negative deleted counts, and exact positive batch counts. `RetentionPruneReport` requires exact booleans, exact datetimes, exact positive prune batch sizes, and exact lists of already-validated `RetentionClassPruneResult` objects. String subclasses, boolean counters, integer subclasses, datetime subclasses, list subclasses, nested dictionaries, negative counts, zero batch counts, and conversion-hook objects fail with `operational store retention report scalar is unsafe` or `operational store retention report results are unsafe` before Pydantic coercion, audit JSON rendering, worker log output, admin reporting, or API serialization can convert malformed maintenance evidence into an official report.

The long-lived worker loop (`python -m jedi_devproject.runtime_worker`) hosts periodic pruning. When retention is enabled, the loop calls the pruner at most once per `JEDI_RETENTION_PRUNE_INTERVAL_SECONDS` (default 3600) and prints the prune report JSON to the worker log for audit capture. One-shot or external schedulers can invoke the same behavior directly through `runtime_worker.prune_operational_store(settings=..., policy=...)` or `store.prune_expired_records(policy=load_retention_policy(os.environ))`.

`prune_operational_store()` rejects invalid direct retention policies before opening the operational store. Embedded callers cannot pass non-positive, non-integer, or boolean `JEDI_RETENTION_ARTIFACT_BLOB_DAYS` or `JEDI_RETENTION_JOB_EVENT_DAYS` values, nor non-positive, non-integer, boolean, or oversized `JEDI_RETENTION_PRUNE_BATCH_SIZE` values. Invalid direct policies fail before store acquisition, PostgreSQL mutation, audit row creation, or runtime report output.

Direct retention pruning also validates the runtime database URL before opening the operational store. `prune_operational_store()` applies the same exact-string and PostgreSQL URL hygiene boundary used by production startup, so malformed direct `RuntimeSettings.database_url` objects, non-PostgreSQL URLs, whitespace/control-character URLs, encoded-control URLs, or fragmented URLs fail before store acquisition, PostgreSQL mutation, audit row creation, or runtime report output.

Runtime worker stdout reports are strict JSON. `_runtime_report_json()` preflights worker loop
summaries, retention prune reports, and stale-job requeue reports with strict JSON numeric handling
before printing them to stdout for log capture. If a corrupted in-process report contains `NaN`,
`Infinity`, or `-Infinity`, report rendering fails with `runtime worker report contains non-finite
numeric values`. The diagnostic does not echo report field names, worker stop reasons, job ids, or
payload values. Unsupported non-JSON report values fail with `runtime worker report contains
non-JSON values`; stdout report rendering does not call `str()` or `repr()` on unsupported objects,
bytes, or custom scalar values. Runtime report keys and text values must be exact strings. String subclasses fail with the same non-JSON diagnostic before stdout serialization. Valid reports continue
to render as compact JSON lines. Runtime report traversal accepts only exact dictionaries, lists,
and tuples; dictionary, list, and tuple subclasses fail before `items()`, iteration, or compact
JSON rendering.

Runtime worker report diagnostics do not retain unsafe causes. Malformed worker loop summaries,
retention prune reports, and stale-job requeue reports still fail with
`runtime worker report contains non-finite numeric values` or
`runtime worker report contains non-JSON values`, but those public `ValueError` instances do not
chain lower-level Pydantic, validation, or JSON encoder exceptions. Crash reporters, traceback
formatters, and worker log serializers therefore cannot re-expose report field names, worker stop
reasons, job ids, credential-like fragments, object type names, or malformed values through
`__cause__`.

Runtime worker float diagnostics do not retain unsafe causes. Malformed worker float settings such as `JEDI_WORKER_IDLE_SLEEP_SECONDS` still fail with fixed parser diagnostics, and hostile parser exceptions still collapse to bounded messages such as `runtime worker raised unstringifiable UnstringifiableWorkerFloatError`, but public worker setting `ValueError` instances do not chain the lower-level parser exception. Startup logs, worker failure records, admin diagnostics, alert payloads, and crash reporters therefore cannot re-expose malformed environment values, parser exception payloads, or hostile exception state through `__cause__`.

`JEDI_RETENTION_PRUNE_INTERVAL_SECONDS` must be greater than zero and `JEDI_RETENTION_PRUNE_INTERVAL_SECONDS<=86400`. Invalid values fail worker settings loading instead of creating a continuous retention maintenance loop or delaying maintenance for days.

### Backup and Restore Runbook

PostgreSQL is the authoritative operational store for lifecycle events, fulfillment jobs, job
events, artifact refs, DB-backed artifact blobs, retention audit rows, and builder maturity evidence.
The ServiceNow instance remains the system of record for stories and customer platform changes, but
JEDI recovery depends on restoring the PostgreSQL operational store to recover queue state, audit
correlation, generated candidate evidence, and update-set handoff history.

retention pruning is not a backup control. Retention windows only delete approved old payload classes
after policy review; they do not protect against database loss, operator error, failed migrations, or
bad deploys. Do not delete `artifact_refs`, `lifecycle_events`, `fulfillment_jobs`, or
`retention_prune_audit` as a storage-management shortcut, because those rows preserve the audit
chain even when large artifact payloads are pruned.

Production deployments must use a customer-approved PostgreSQL backup service with encryption at
rest, encryption in transit, access logging, and point-in-time recovery. Set the engagement's RPO and
RTO in the customer operations plan before production traffic is enabled. For the MVP sidecar, the
default recommendation is an RPO of 15 minutes or better and an RTO of 4 hours or better, unless the
customer ATO, cloud service, or project criticality requires stricter values.

Minimum operational procedure:

- Schedule automated PostgreSQL backups and WAL/PITR retention in the hosting environment.
- Protect backup credentials in the same approved secret manager used for runtime secrets.
- Run `python3 -m jedi_devproject.cli init-operational-store --env-file .env` after restoring into
  a staging database to verify packaged migrations and schema readiness.
- Start the API against the restored staging database and confirm `GET /ready` returns ready.
- Query `GET /admin/operations` with the admin bearer token and compare queue counts against the
  pre-restore incident timeline.
- Inspect at least one restored lifecycle event, fulfillment job, job event timeline, and artifact
  ref chain before declaring the restore successful.
- Record the restore drill date, operator, source backup timestamp, target database, observed RPO,
  observed RTO, `/ready` result, `/admin/operations` summary, and any exceptions in the customer
  operations evidence repository.

Run a restore drill before go-live and after any material change to the database service, migration set, retention policy, backup provider, or deployment topology. No production deployment is ready until a restore drill proves that the API can start against restored data, schema readiness is green, and the operator can trace a restored story from lifecycle event to fulfillment job to artifact refs.

## Lifecycle Webhook API

The local runtime exposes a FastAPI application from `create_lifecycle_api()` in `jedi_devproject.lifecycle_api`. Production wiring must provide `DATABASE_URL` for `connect_operational_store(database_url=...)`, then inject that store into the API factory.

`create_lifecycle_api()` rejects invalid `max_request_body_bytes` values at app construction. Direct lifecycle API wiring cannot pass zero, negative, boolean, or non-integer body limits and still start a FastAPI app; invalid values fail with `ValueError` before route registration or request handling. Runtime entrypoints still apply the stricter environment-backed production ceilings for `JEDI_LIFECYCLE_WEBHOOK_MAX_BODY_BYTES`.

Deployment probes:

```text
GET /health
GET /ready
```

`GET /health` is a cheap liveness probe and only returns `{"status":"ok"}`. `GET /ready` is a readiness probe on the runtime API wrapper. It performs a minimal read-only operational-store query and returns `200` with `status=ready` when PostgreSQL-backed state is reachable. If the store check fails, it returns `503` with `status=unready` and a failed `operational_store` check without returning exception text, database URLs, credentials, or other diagnostic secrets.

Operational store schema readiness is explicit. `GET /ready` checks packaged migration tables with
`verify_schema_ready()` before advertising the API as ready. If PostgreSQL is reachable but required
tables from the packaged migrations are missing, readiness returns `503` with
`operational_store_schema=missing`. This distinguishes a migration/bootstrap problem from a general
database connectivity failure while still avoiding exception text, SQL text, database URLs, or
credential leakage in the public response.

Operational store schema readiness rows are exact-shape guarded. `verify_schema_ready()` accepts only exact dictionary rows from the `information_schema.tables` query, and `table_name` values must be absent, `None`, or exact strings. Dictionary subclasses, mapping-like objects, string subclasses, and malformed table-name values fail with `operational store schema readiness row contains non-JSON value` before readiness-table matching, API readiness responses, admin health checks, startup probes, or logs can execute caller-controlled row hooks.

Operational store surface maturity evidence rows are exact-shape guarded. `builder_maturity_evidence_for_surface()` accepts only exact dictionary aggregate rows from the read-only maturity query, and `samples`, `successes`, and `failures` must be exact integers. Dictionary subclasses, mapping-like objects, boolean values, integer subclasses, floats, strings, and hostile numeric objects fail with `operational store surface maturity row contains non-JSON value` before maturity scoring, automation-threshold checks, admin reporting, or work-note routing can execute caller-controlled row or numeric hooks.

Operational store surface maturity evidence records are exact-scalar guarded as well. `SurfaceMaturityEvidenceRecord` requires an exact string surface name and exact non-negative integer `samples`, `successes`, and `failures` counts. String subclasses, boolean counts, integer subclasses, floats, strings, negative counts, and conversion-hook objects fail with `operational store surface maturity record scalar is unsafe` before Pydantic coercion, maturity scoring, automation-threshold decisions, admin reporting, API serialization, or work-note routing can turn malformed scoring evidence into official maturity state.

Operational store list read rows are exact containers before API, admin, or worker read models are hydrated. `requeue_stale_running_jobs()`, `job_events_for_job()`, `recent_lifecycle_events()`, `recent_fulfillment_jobs()`, and `artifact_refs_for_job()` require exact list results containing exact dictionary rows. List subclasses, alternate sequences, dictionary subclasses, mapping-like objects, and malformed rows fail with `operational store read rows contain non-JSON value` before row iteration, Pydantic model validation, admin timeline rendering, stale-job requeue reporting, artifact reference rendering, or API JSON serialization can execute caller-controlled row hooks.

Operational store single read rows are exact dictionaries before API, admin, or worker read models are hydrated or indexed. Lifecycle event lookup, fulfillment job creation and transitions, artifact reference creation, artifact blob creation and lookup, and retention prune count reads route returned `fetch_one()` rows through `_operational_read_row()` after normal missing-row handling. Dictionary subclasses, mapping-like objects, alternate row containers, and malformed rows fail with `operational store read row contains non-JSON value` before row indexing, Pydantic model validation, artifact id extraction, retention count conversion, admin detail rendering, worker status reporting, or API JSON serialization can execute caller-controlled row hooks.

Operational store scalar reads are exact integer guarded where database-returned identifiers or counters drive follow-on writes. Artifact blob id extraction requires an exact positive integer before creating the linked `artifact_refs` row, and retention prune count reads require exact non-negative integers before audit totals, batch-loop decisions, or prune reports are calculated. Booleans, integer subclasses, floats, strings, objects with conversion hooks, missing scalar fields, zero or negative artifact ids, and negative prune counts fail with `operational store read scalar is unsafe` before `int()` coercion, artifact reference insertion, retention audit writes, loop termination checks, admin reporting, or API JSON serialization can consume malformed database scalar behavior.

Operational store record hydration is exact-scalar guarded before Pydantic model validation. Lifecycle events, fulfillment jobs, job events, artifact refs, and artifact blobs require exact string values for text fields, exact integers for ids and counters, exact datetimes for timestamp fields, and exact JSON dictionaries/lists/scalars for persisted JSON payloads. String subclasses, integer subclasses, boolean ids or counters, datetime subclasses, mapping/list subclasses, non-finite floats in payloads, and conversion-hook objects fail with `operational store record scalar is unsafe` or `operational store record payload is unsafe` before Pydantic coercion, model serialization, admin rendering, API JSON serialization, work-note routing, worker status reporting, or artifact reference reporting can execute caller-controlled scalar or container behavior.

Operational store record payload traversal is cycle-safe and depth-bounded. Persisted JSON payload validation tracks active exact dictionaries and lists and caps traversal at 32 levels. Cyclic payloads, repeated active containers, and excessively nested payloads fail with `operational store record payload is unsafe` before recursive validation, Pydantic model hydration, admin rendering, API JSON serialization, work-note routing, worker status reporting, or artifact reference reporting can recurse indefinitely or expose payload fragments through traversal failures.

Use `init-operational-store` to initialize or upgrade the PostgreSQL operational store before
opening a hosted service to traffic:

```bash
python3 -m jedi_devproject.cli init-operational-store --env-file .env
```

The command loads the same runtime settings as the API and worker, opens the operational store,
applies the packaged migrations through the existing store initialization path, then verifies schema
readiness. A successful run prints only `operational_store_schema_ready=true`. If required migration
tables are still missing, it prints `operational_store_schema_ready=false` and exits non-zero. The
command does not print `DATABASE_URL`, ServiceNow credentials, model provider credentials, or raw
database errors.

Every runtime response returns `X-JEDI-Request-ID` for proxy, application, and operator-log correlation. If an inbound `X-Request-ID` is present, printable ASCII, and no longer than 128 characters, the runtime echoes it as `X-JEDI-Request-ID`. Missing, empty, overlong, or non-printable request ids are replaced with a generated UUID4. The request id is correlation metadata only; it is not authentication, authorization, idempotency, or proof that two requests share the same lifecycle event.

The lifecycle receiver is:

```text
POST /lifecycle/events
```

A valid `Draft` to `Ready` `LifecycleStateChangeEvent` returns `202 Accepted`, records the event in `lifecycle_events`, enqueues one `fulfillment_jobs` row, and returns the queued `job_id`. A valid `Ready for Testing` to `Complete` event records the event, writes a `story_completed` audit entry against the latest fulfillment job for that story, and updates the story `u_ai_status=Complete` by `story_sys_id` without enqueueing another build. A valid `Ready for Testing` to `Ready` event records `rework_requested` against the latest fulfillment job without enqueueing another build. A valid `Ready for Testing` to `Draft` event marks the latest fulfillment job `rejected` and preserves artifacts for audit instead of deleting evidence. Unsupported lifecycle transitions are still accepted and recorded, but they are not enqueued for fulfillment.

Lifecycle webhook schema validation errors do not echo rejected payload values. HTTP 422
responses preserve structured validation type, location, and message metadata for operator
debugging, but omit Pydantic `input` fields so malformed lifecycle requests cannot reflect
ServiceNow sys_ids, work notes, credentials, or other submitted payload fragments back to callers.
Malformed lifecycle webhook JSON and invalid UTF-8 request bodies both return the same stable
`invalid lifecycle webhook JSON` diagnostic without echoing submitted body fragments. Non-standard
JSON numeric constants such as `NaN`, `Infinity`, and `-Infinity` use that same invalid-JSON path
before lifecycle schema validation, event recording, or job enqueue. HMAC authentication still signs
and verifies the exact raw request body before JSON decoding.

Lifecycle webhook payload diagnostics do not retain unsafe causes. Malformed JSON still fails with `invalid lifecycle webhook JSON`, and schema validation still returns sanitized Pydantic error details such as `extra_forbidden` without rejected input values, but the public `HTTPException` values do not chain JSON parser or Pydantic validation exceptions. API error serialization, runtime logs, work notes, and crash reporters therefore cannot re-expose raw request body fragments, parser offsets, or rejected lifecycle payload values through `__cause__`.

Lifecycle HMAC timestamp diagnostics do not retain unsafe causes. Invalid HMAC timestamp values still fail with `lifecycle webhook timestamp invalid`, including all-digit values that reach Python integer parsing but exceed the interpreter conversion limit. The public `HTTPException` does not chain the lower-level `ValueError`, so API error serialization, runtime logs, work notes, and crash reporters cannot re-expose oversized timestamp fragments, parser limit details, or malformed credential material through `__cause__`.

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

The signature base string is `<timestamp>.<raw request body>`, signed with `HMAC-SHA256` using `JEDI_LIFECYCLE_WEBHOOK_SECRET`. The receiver verifies the timestamp replay window before validating the event payload and rejects missing signatures with `401` and bad signatures with `403`. The receiver accepts `sha256=<hex hmac>` for generic clients and `sha256-base64=<base64 hmac>` for ServiceNow emitters because ServiceNow's `GlideCertificateEncryption.generateMac()` returns Base64 MAC output. HMAC signature headers must match one of those two exact shapes before constant-time comparison: `sha256=` followed by 64 hexadecimal characters, or `sha256-base64=` followed by a Base64 value that decodes to a 32-byte SHA-256 MAC.

Production public roles reject `JEDI_LIFECYCLE_WEBHOOK_MAX_SKEW_SECONDS` values above `900`
seconds. Keep the default `300` second replay window unless a documented ServiceNow clock-skew or
edge-routing issue requires a wider value.

Inbound lifecycle webhook credential material is never normalized. Timestamp header values must be ASCII base-10 digits without padding, whitespace, or control characters before integer parsing. HMAC signature values and interim shared-secret values are rejected before constant-time comparison when they are non-ASCII, padded, whitespace-bearing, or control-character-bearing. Timestamp, HMAC signature, and interim shared-secret header values are also capped at 8 KiB before integer parsing or constant-time comparison, with the cap measured on ASCII bytes. This keeps ServiceNow emitter bugs, proxy rewriting mistakes, copied test values, non-ASCII credential probes, and oversized credential probes from becoming ambiguous authenticated requests or expensive ingress work.

The configured lifecycle webhook signing secret is validated against the same credential syntax boundary before request authentication runs. Empty secrets still fail as unconfigured, while non-ASCII, padded, whitespace-bearing, control-character-bearing, or oversized configured secrets fail closed as invalid runtime configuration with `503`. This keeps direct API construction, development deployments, and future alternate config loaders aligned with production startup validation.

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
GET /jobs/{job_id}/events
GET /admin/lifecycle-events
GET /admin/jobs
GET /admin/alerts
```

`GET /artifacts/{artifact_id}` returns artifact metadata plus the JSON payload stored in `artifact_blobs`. It includes the source `event_id` and `correlation_id` from the associated fulfillment job so operators can join the artifact back to the lifecycle event and ServiceNow work notes. It returns `404` when the artifact id is not found.

`GET /jobs/{job_id}/artifacts` returns the requested job's `event_id`, story number, `correlation_id`, and artifact references, including `artifact_id`, `artifact_kind`, `path`, and SHA-256 hash. `GET /jobs/{job_id}/events` returns the same job correlation metadata plus the ordered `job_events` timeline. Job event diagnostic messages are redacted before the API returns them.

Admin artifact payloads are diagnostic views, not raw evidence export. `GET /artifacts/{artifact_id}` and `/admin/artifacts/{artifact_id}` recursively redact stored payload values before returning them. Secret-bearing keys such as `client_secret` and `api_key` are replaced with redaction markers, and diagnostic strings inside artifact payloads are redacted for URL passwords, sensitive query values, authorization headers, cookies, and private-key blocks. Job artifact reference paths returned by `GET /jobs/{job_id}/artifacts` are also diagnostic strings and are redacted before returning them. The artifact SHA-256 remains the provenance check for the unredacted stored payload.

Admin not-found diagnostics do not retain unsafe causes. Missing artifact lookups still return `artifact not found`, and missing job lookups still return `job not found`, but public admin `HTTPException` values do not chain lower-level runtime-store `KeyError` objects. JSON admin APIs, the HTML admin console, logs, work notes, alert payloads, and crash reporters therefore cannot re-expose store lookup keys, alternate store exception text, or persistence-layer details through `__cause__`.

`GET /admin/lifecycle-events` returns the most recent lifecycle event summaries with event id, event type, story number, received timestamp, and validation status. It intentionally does not return raw event payload JSON or ServiceNow sys_ids. `GET /admin/jobs` returns the most recent fulfillment job summaries with status, attempt count, lock metadata, and the latest error text.

`GET /admin/alerts` returns Operational Alerts as a read-only projection over recent fulfillment jobs. It does not create a separate mutable alert queue. The MVP projection includes failed and rejected fulfillment jobs, plus stale running jobs, preserves `job_id`, `event_id`, story number, `correlation_id`, status, attempt count, update timestamp, severity, and operator action, and redacts diagnostic detail before returning it. Operators should use the alert's job id to inspect `/jobs/{job_id}/events`, the related ServiceNow work notes, and worker logs.

Admin list endpoints reject non-positive `limit` values before operational-store access. `GET /admin/lifecycle-events`, `GET /admin/jobs`, and `GET /admin/alerts` return `422` with `admin result limit must be a positive integer` for zero or negative limits. Positive limits above 100 are still capped to 100 so diagnostic views cannot request unbounded result sets.

The HTML admin console treats alert response fields as untrusted in-process diagnostics. Alert rows
render `severity` and `detail` only when those projected fields are exact strings. Malformed,
string-subclass, non-string, or unstringifiable projected values collapse to fixed fallback text
before HTML escaping, so a corrupted alert projection cannot execute custom `__str__` hooks or leak
operator diagnostic fragments while rendering `/admin`.

Persisted admin diagnostic strings are whitespace/control-character-normalized and bounded after
redaction before they are returned by JSON APIs or rendered in the HTML console. This applies to
fulfillment job `last_error` values, job event messages, artifact reference paths, operational alert
details, and string values inside artifact payload diagnostic views. Long values are truncated with
`...[truncated]` after the same redaction and normalization rules run, so stored provider output,
worker failures, or malformed external responses cannot retain raw multiline diagnostic text or
create oversized admin responses while the artifact SHA-256 still preserves provenance for the
original stored payload.

Oversized artifact payload diagnostic views are collapsed as a whole after recursive redaction.
When the redacted payload JSON would exceed the admin diagnostic payload cap, the API returns
`payload_truncated: true` and replaces `payload` with a bounded preview containing
`original_payload_type`, `diagnostic_preview`, and `truncated: true`; the HTML artifact page renders
the same bounded projection. The original artifact row is not modified, and the SHA-256 remains the
operator's provenance handle for the full stored payload.

Artifact payload diagnostic projection also bounds collection traversal before serialization. Large
arrays and objects are sampled up to the admin collection-item cap and include deterministic
`omitted_items` or `omitted_fields` markers before the preview is serialized. This prevents a large
JSON artifact from forcing the admin API to recursively redact or serialize every nested entry just
to decide that the diagnostic view must be truncated. The projection samples dictionaries, arrays,
and tuples through bounded iterators instead of materializing full collection copies before applying
the cap.

All admin diagnostic surfaces share the same admin rate limiter. This includes JSON admin endpoints, artifact APIs, the HTML admin console at `/admin`, and Basic-auth artifact detail pages under `/admin/artifacts/{artifact_id}`. The limiter runs before admin token or Basic-auth credential checks, so repeated console requests and repeated artifact view requests are throttled even during credential guessing.

Rate-limit bucket keys are bounded before storage. Safe printable ASCII keys up to 256 bytes
are preserved for operator readability, while oversized, whitespace-bearing,
control-character-bearing, or non-ASCII keys are replaced with deterministic `sha256:<digest>`
bucket identifiers before lookup or insertion into the in-memory limiter. This prevents malformed
client host/path material or future caller-provided identifiers from storing raw secrets, control
characters, or unbounded strings in rate-limit state.

`InMemoryRateLimiter.check()` rejects non-exact-string keys before clock reads, hashing, bucket
pruning, or bucket state access. Direct callers cannot pass bytes, nulls, numeric values, string
subclasses, or objects with caller-controlled string methods as rate-limit bucket keys; invalid keys
fail with `rate limit key must be an exact string`.

Rate-limit state is also bounded by bucket count. The in-memory limiter prunes expired buckets on
each check and defaults to at most 10000 live buckets. When a new bucket arrives while the limiter
is still at capacity after pruning, the request is assigned to a shared `rate-limit-overflow`
bucket instead of creating another per-client bucket. This keeps high-cardinality client source
patterns from creating unbounded process memory growth while preserving deterministic throttling.
`InMemoryRateLimiter` rejects boolean and non-integer direct controls before range checks or bucket
state initialization. Direct callers cannot pass `True`, strings, floats, or custom numeric-looking
objects for `max_requests`, `window_seconds`, or `max_buckets`; invalid values fail with stable
diagnostics such as `max_requests must be an integer`, `window_seconds must be an integer`, or
`max_buckets must be an integer`.
Configured lifecycle and admin bucket caps must also stay at or below 100000 buckets. Values above
that hard ceiling fail runtime validation before API construction, so an environment typo cannot
silently disable the memory boundary.
Configured lifecycle and admin request caps must stay at or below 10000 requests per bucket.
Values above that ceiling fail runtime validation before API construction and are also rejected by
the shared limiter constructor, so an environment typo cannot make each bucket retain an
unbounded number of request timestamps.
Configured lifecycle and admin rate-limit windows must stay at or below 86400 seconds. Values above
that ceiling fail runtime validation before API construction and are also rejected by the shared
limiter constructor, so an environment typo cannot make limiter buckets retain timestamp state
longer than one day.
The limiter also clamps observed process time so it never moves backward within a running process.
If the system clock moves backward, retry calculations and stored timestamps use the last observed
limiter time instead of the lower clock value. This prevents inflated `Retry-After` values and
older timestamp insertion after clock adjustments.
`InMemoryRateLimiter` rejects invalid clock values before bucket storage. Injected clock callbacks
must return finite non-negative integers or floats; booleans, strings, `NaN`, infinities, and
negative timestamps fail with `rate limit clock must return a finite non-negative number` before
`_last_now` or bucket timestamp state is updated.
`InMemoryRateLimiter` rejects non-callable clock dependencies before limiter state initialization.
Direct callers cannot pass nulls, booleans, numbers, strings, or other non-callable objects as the
clock dependency; invalid clocks fail with `rate limit clock must be callable`.
`_require_admin_rate_limit` validates limiter decision objects before `Retry-After` header construction.
Malformed admin limiter dependencies fail closed with `admin rate limiter is invalid` instead of
returning a raw runtime error, bypassing the limiter, or emitting an invalid retry header.
`_require_rate_limit` validates lifecycle limiter decision objects before lifecycle `Retry-After`
header construction. Malformed lifecycle limiter dependencies fail closed with
`lifecycle rate limiter is invalid` instead of recording webhook events behind a broken limiter or
emitting invalid retry metadata.

Limiter checks are serialized inside each process. The shared in-memory limiter protects bucket
lookup, pruning, admission, retry calculation, and timestamp append with one critical section, so
concurrent lifecycle or admin requests cannot both observe the same pre-admission bucket state and
over-admit beyond the configured per-bucket request cap.

Runtime request validation errors do not echo rejected input values. Framework-generated HTTP 422
responses for malformed path or query parameters preserve validation type, location, and message
metadata, but omit Pydantic/FastAPI `input` fields. This prevents malformed admin diagnostic
requests such as invalid `limit` query values from reflecting credentials, ServiceNow sys_ids, or
other caller-controlled fragments before route-level admin authentication runs.

Development Basic auth is bounded before credential parsing. The runtime rejects Basic auth payloads whose encoded credential section is larger than 8192 bytes before base64 decoding, so malformed or oversized console authentication attempts cannot create an unbounded decode path. It also rejects padded, whitespace-bearing, or control-character-bearing encoded credential sections before base64 decoding instead of trimming them. After decoding, username and password parts are also rejected before constant-time comparison when either part is padded, whitespace-bearing, or control-character-bearing. This control is in addition to admin route body-size limits and rate limiting.

Admin console settings loading and request-time Basic-auth parsing share bounded credential policy. Configured `JEDI_ADMIN_CONSOLE_USERNAME` and `JEDI_ADMIN_CONSOLE_PASSWORD` values are rejected during settings loading when either value is larger than 8192 bytes, padded, control-character-bearing, or otherwise malformed. The request-time decoded username and password parts use the same `MAX_BASIC_AUTH_CREDENTIAL_BYTES` policy, so local development console configuration cannot accept credentials that the admin console boundary would later reject.

Direct `RuntimeSettings.admin_console_username` and `RuntimeSettings.admin_console_password` validation is exact-string guarded before production role-policy checks. `validate_runtime_settings()` rejects admin console credential string subclasses or non-string objects with `<SETTING> must be a string runtime setting` before development-only production rejection, worker/api role checks, truthiness checks, or credential comparison setup. This keeps local development Basic-auth credentials from carrying malformed direct runtime objects into production startup validation.

Request-time admin authentication also exact-string validates configured admin auth settings before credential parsing or constant-time comparison. `_require_admin_token()` rejects malformed direct `RuntimeSettings.admin_api_token` values as `503 admin artifact API token is invalid`, and `_require_admin_console_credentials()` rejects malformed direct `RuntimeSettings.admin_auth_mode`, `RuntimeSettings.runtime_environment`, `RuntimeSettings.admin_console_username`, or `RuntimeSettings.admin_console_password` values as `503 admin console configuration is invalid`. These request-time checks run before Basic-auth decoding, bearer-token comparison, admin-auth mode equality checks, configured credential truthiness checks, or username/password comparison, so embedded runtimes cannot execute custom string, length, truthiness, or equality hooks while authenticating operators.

The encoded Basic-auth section validation also lives in shared policy. Request-time admin console authentication rejects padded, whitespace-bearing, control-character-bearing, non-ASCII, or larger-than-8192-byte encoded credential sections through the same Basic-auth policy module that owns `MAX_BASIC_AUTH_ENCODED_BYTES`; this keeps pre-decode rejection behavior aligned with the documented credential limits.

Basic-auth encoded credential sections are ASCII-only before decoding. Non-ASCII encoded
payloads are rejected before Base64 decoding and before constant-time comparison, and the
8192-byte cap is measured on the encoded ASCII bytes. This prevents malformed Basic-auth
headers from entering implementation-defined Base64 parser behavior or producing
unhandled non-ASCII parser errors.

Admin Bearer tokens are also bounded before credential comparison. The runtime rejects Bearer token values larger than 8192 bytes before calling constant-time comparison, so oversized token probes cannot create an unbounded comparison path. It also rejects padded, whitespace-bearing, or control-character-bearing Bearer token values before comparison instead of trimming them. Normal token mismatches, malformed token values, and oversized token attempts return the same rejected-token response.

Runtime settings loading rejects padded or control-character `JEDI_ADMIN_API_TOKEN`
values before settings are returned, so configured admin bearer secrets cannot be
silently normalized or pass log-injection characters into admin diagnostic auth paths.
Blank or absent token values remain unconfigured and keep the admin artifact API
fail-closed. The admin authentication boundary also validates the configured admin bearer token
before comparing inbound credentials. If an alternate settings loader
or direct `RuntimeSettings` construction bypasses normal settings validation,
non-ASCII, padded, control-character-bearing, or larger-than-8192-byte configured
admin bearer token values fail closed as invalid runtime configuration with `503`
before any inbound token comparison runs.

Production startup validation rejects weak or malformed configured admin API tokens. If `JEDI_ADMIN_API_TOKEN` is set while `JEDI_ENVIRONMENT=production`, `JEDI_ADMIN_API_TOKEN` must be at least 32 characters, `JEDI_ADMIN_API_TOKEN` must be at most 8192 bytes, `JEDI_ADMIN_API_TOKEN` must contain only ASCII characters, the value must not contain whitespace or control characters, oversized configured bearer secrets fail before the API starts, and non-ASCII configured bearer secrets fail before the API starts. Worker-only validation paths may omit the token, but they cannot silently accept a short or malformed production token value, nor an oversized or non-ASCII production token value, that would later be used by JSON admin diagnostics.

Admin bearer token policy is centralized so startup validation and request-time auth share one bearer token ceiling. The runtime config layer imports the same `MAX_ADMIN_BEARER_TOKEN_BYTES` value used by API bearer-token parsing, which prevents production startup checks from drifting behind fail-closed request handling.

Admin job diagnostic path parameters are validated before operational-store lookup. `/jobs/{job_id}/artifacts` and `/jobs/{job_id}/events` reject empty, whitespace-padded, non-printable, non-ASCII, or longer-than-256-character job identifiers with `400 invalid job id`. This prevents malformed operator requests from creating unbounded lookup keys or passing decoded control characters into diagnostics while preserving normal generated job ids.

Admin diagnostic responses are non-cacheable. JSON admin endpoints, artifact APIs, the HTML admin console, and Basic-auth artifact detail pages return `Cache-Control: no-store`, `Pragma: no-cache`, and `Expires: 0` so browsers, legacy proxies, and shared operator workstations do not retain diagnostic payloads, artifact metadata, redacted error views, or failed admin authentication responses. Runtime responses also return `X-Content-Type-Options: nosniff`; liveness and readiness probes receive `nosniff` without forcing no-store semantics.

Authenticated admin diagnostic responses also return `Vary: Authorization`. This keeps shared HTTP caches and intermediate proxies from treating one operator's Bearer-token or Basic-auth diagnostic response as reusable for another credential context. Public deployment probes such as `/health` do not emit `Vary: Authorization`.

Admin diagnostic responses also return `X-Robots-Tag: noindex, nofollow, noarchive`. This is not an access-control mechanism, but it reduces blast radius if an admin diagnostic URL is exposed to a crawler, enterprise search appliance, or browser-adjacent indexing tool. Public deployment probes such as `/health` do not emit the robots policy.

HTML admin console responses also use browser isolation headers. `/admin` and `/admin/artifacts/{artifact_id}` return a restrictive `Content-Security-Policy` with `default-src 'none'`, `script-src 'none'`, `connect-src 'none'`, `object-src 'none'`, `base-uri 'none'`, `form-action 'none'`, and `frame-ancestors 'none'`; inline style is the only allowed browser resource because the console renders self-contained server-side HTML. The same HTML surfaces return `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, and a `Permissions-Policy` that disables browser capabilities including camera, microphone, geolocation, payment, USB, motion sensors, and fullscreen. JSON admin diagnostic endpoints do not receive the HTML CSP or HTML Permissions Policy.

Strict Transport Security is explicit and deployment-controlled. By default, development and
worker-only runtimes do not emit `Strict-Transport-Security`, which keeps local HTTP development and
non-final proxy topologies reversible. Public production roles, `JEDI_RUNTIME_ROLE=api` and
`JEDI_RUNTIME_ROLE=combined`, fail startup unless `JEDI_STRICT_TRANSPORT_SECURITY_ENABLED=true` is
configured. Set it only after the public deployment is permanently HTTPS at the approved edge. When
enabled, every runtime response returns `Strict-Transport-Security: max-age=31536000; includeSubDomains` by default. Override the duration with `JEDI_STRICT_TRANSPORT_SECURITY_MAX_AGE_SECONDS=<seconds>`. Public production roles require at least `31536000` seconds; lower values fail startup instead of silently weakening the HSTS policy. Invalid non-positive production values also fail startup validation.

Stale running job detection is non-mutating. It does not fail, retry, unlock, or requeue work from the admin API because a worker may still own the job. The default threshold is one hour and can be configured with:

```text
JEDI_RUNNING_JOB_STALE_AFTER_SECONDS=<positive seconds, default 3600>
```

Authenticated JSON diagnostics expose the aggregate operational view at:

```text
GET /admin/operations
Authorization: Bearer <JEDI_ADMIN_API_TOKEN>
```

The response is DB-backed and reports fulfillment-job counts for `queued`, `running`, `completed`,
`failed`, `rejected`, `stale_running`, and `total`, plus the configured
`running_job_stale_after_seconds` threshold. This endpoint uses aggregate SQL against
`fulfillment_jobs`; it does not infer backlog or stale-running status from the paginated
`/admin/jobs` list.

Production startup caps `JEDI_RUNNING_JOB_STALE_AFTER_SECONDS<=86400`; higher values fail startup
so stale-job visibility cannot be disabled for days by configuration.

Worker-side stale recovery is separate and disabled by default. When explicitly enabled, the long-running worker periodically calls `requeue_stale_running_jobs()` on the PostgreSQL operational store. The store selects stale `running` jobs with `FOR UPDATE SKIP LOCKED`, updates them back to `queued`, clears `locked_by`, `locked_at`, and `last_error`, preserves `attempt_count`, and appends a `queued` `job_events` audit entry. This makes recovery bounded, idempotent, and visible in the job event timeline.

`requeue_stale_running_jobs()` rejects invalid direct controls before opening the operational store. Embedded callers cannot pass non-positive, non-integer, boolean, or oversized `JEDI_RUNNING_JOB_STALE_AFTER_SECONDS` values, nor non-positive, non-integer, boolean, or oversized `JEDI_STALE_JOB_REQUEUE_BATCH_SIZE` values. Invalid direct controls fail before stale cutoff calculation, store acquisition, PostgreSQL mutation, or runtime report output.

Direct stale-job recovery also validates the runtime database URL before opening the operational store. `requeue_stale_running_jobs()` applies the same exact-string and PostgreSQL URL hygiene boundary used by production startup, so malformed direct `RuntimeSettings.database_url` objects, non-PostgreSQL URLs, whitespace/control-character URLs, encoded-control URLs, or fragmented URLs fail before stale cutoff calculation, store acquisition, PostgreSQL mutation, job-event audit insertion, or runtime report output.

```text
JEDI_STALE_JOB_REQUEUE_ENABLED=false
JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS=3600  # maximum 86400
JEDI_STALE_JOB_REQUEUE_BATCH_SIZE=10  # maximum 100
```

`JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS` must be greater than zero and `JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS<=86400`. `JEDI_STALE_JOB_REQUEUE_BATCH_SIZE` must be greater than zero and `JEDI_STALE_JOB_REQUEUE_BATCH_SIZE<=100`, so maintenance cannot create unbounded lock or write bursts. Invalid values fail worker settings loading instead of being coerced to defaults, because silent recovery configuration changes make incident handling harder to audit.

Enable stale recovery only when the deployment has one operational owner for recovery policy. Do not enable multiple independent external recovery scripts against the same operational store.

## External Alert Delivery

External alert delivery is disabled by default. Sprint 173 added the webhook delivery primitive, Sprint 174 wires failed worker iterations to that primitive, Sprint 175 wires stale-job recovery alerts when recovery actually requeues one or more jobs, and Sprint 176 wires rejected-job alerts when a ServiceNow lifecycle event moves a story from `Ready for Testing` back to `Draft`. Successful, idle, rework-requested, zero-requeue stale recovery sweeps, and retention-prune iterations do not emit external alerts.

Stale-job recovery alerts preserve the total requeued count, but their generated detail text previews at most 50 job ids and appends an omitted-count marker for the rest. This bounds alert construction before webhook serialization and keeps large recovery batches from creating unbounded operator diagnostics.

Stale-job recovery alert details are also redacted and capped at 16 KiB with the standard alert truncation marker. The job-id preview count is not treated as a sufficient size control because a single upstream job id can still be unexpectedly large.

Worker-failure and rejected-job alerts redact diagnostic text before storing it in the generated alert detail, then cap that detail at 16 KiB with the standard alert truncation marker. This keeps oversized upstream exceptions or lifecycle rejection reasons from making the alert undeliverable before webhook body-size validation.

Generated alert constructors reject unsafe metadata before returning an `ExternalAlert`. Worker-failure alerts validate the source job id and story number, rejected-job alerts validate the source job id, event id, story number, and correlation id, and stale-requeue alerts validate the generated source metadata for the single-job or multi-job case. The final generated alert is also passed through the same timestamp, body text, routing, and webhook-header metadata validators used by delivery. This prevents queued alert objects from carrying header-injection characters, blank or padded ids, or oversized routing metadata that would only fail at send time.

```text
JEDI_ALERT_WEBHOOK_ENABLED=false
JEDI_ALERT_WEBHOOK_URL=<https webhook URL>
JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS=3
JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES=16384
```

When alert webhooks are enabled in production, `JEDI_ALERT_WEBHOOK_URL` is required, must use HTTPS, must not include raw whitespace or control characters, must not include percent-encoded whitespace or control characters such as `%0d`, `%0a`, or `%20`, must not include embedded URL credentials such as `https://user:password@example.gov/hook`, must not include URL fragments, must not target obvious local or link-local SSRF destinations such as `localhost`, delegated `.localhost` names such as `alerts.localhost`, Unicode-dot local names such as `localhost。`, `127.0.0.1`, Unicode-dot loopback forms such as `127。0。0。1`, `[::1]`, unspecified bind addresses such as `0.0.0.0` or `[::]`, legacy numeric loopback forms such as `127.1`, `2130706433`, `0177.0.0.1`, or `0x7f000001`, legacy numeric link-local forms such as `2852039166`, or `169.254.169.254`, and must not include sensitive query parameters such as `token`, `access_token`, `accessToken`, `signature`, `api-key`, `x-api-key`, `awsSecretAccessKey`, `azureClientSecret`, `client-secret`, `clientSecret`, `x-client-secret`, `private_key`, `cookie`, or `client_secret`. Sensitive alert webhook query validation treats both ampersand-separated and semicolon-separated parameters as candidates, so `team=platform;token=secret` and `team=platform;client_secret=secret` are rejected before startup or delivery. It also evaluates percent-decoded query separators, so `team=platform%26token=secret` and `team=platform%3Bclient_secret=secret` are rejected while benign values such as `note=fish%26chips` remain allowed. Query separator decoding is bounded to three decode passes, so double-encoded separators such as `team=platform%2526token=secret` and `team=platform%253Bclient_secret=secret` are also rejected without making URL validation an unbounded CPU path. Runtime settings loading rejects configured `JEDI_ALERT_WEBHOOK_URL` values that are padded, contain control characters, use non-HTTPS schemes, include credentials, fragments, local targets, encoded whitespace/control characters, or sensitive query parameters, even when alert delivery is disabled. Runtime startup validation rejects missing, non-HTTPS, credentialed, fragmented, and sensitive-query alert webhook URLs before the API or worker starts; it also rejects whitespace/control-character, encoded-whitespace/control-character, local-target, link-local-target, unicode-dot local-target, and legacy-numeric local-target alert webhook URLs. Timeout and body-size settings must be greater than zero. The delivery primitive refuses unsafe URLs and oversized payloads before sending, posts compact JSON with `Content-Type: application/json`, and redacts sensitive response values before raising delivery errors. Alert outbound summary, detail, and operator-action text is redacted, whitespace/control-character-normalized, and bounded before compact JSON bytes are sent, so direct `emit_alert_webhook()` callers cannot bypass generated-alert sanitization. Alert sink response redaction covers both structured secret-bearing keys and plain diagnostic strings containing values such as `client_secret=value`, `client-secret=value`, `aws_secret_access_key=value`, `Set-Cookie: value`, PEM private-key blocks, URL passwords, or sensitive query parameters. Alert sink response string values are also whitespace/control-character-normalized before `AlertDeliveryError` diagnostics are formatted. Structured response redaction uses the shared sensitive-key vocabulary, including `api_key`, `api-key`, `x-api-key`, `aws_secret_access_key`, `awsSecretAccessKey`, `awsSessionToken`, `azureClientSecret`, `token`, `signature`, `secret`, `id_token`, `idToken`, `client_secret`, `clientSecret`, `client-secret`, `x-client-secret`, `private_key`, `privateKey`, `ssh_private_key`, `Cookie`, `Set-Cookie`, `access_token`, and `accessToken`, so sink-specific error payloads cannot leak common credential names through operator diagnostics. Worker alert delivery is best-effort: delivery failures increment `alert_failures` in the worker loop summary, log a warning with diagnostic redaction, and do not crash the worker or change the authoritative PostgreSQL job state. Lifecycle rejected-job alert delivery is also best-effort: delivery failures are logged with diagnostic redaction but do not block lifecycle webhook acceptance after PostgreSQL records the rejected terminal job. Stale-requeue and rejected-job alerts use `warning` severity and tell operators to inspect job events, candidate artifacts, ServiceNow work notes, and worker logs before assuming recovery or rejection handling is complete.
Direct `RuntimeSettings.alert_webhook_url` validation is exact-string guarded before enabled-alert checks. `validate_runtime_settings()` rejects alert webhook URL string subclasses or non-string objects with `JEDI_ALERT_WEBHOOK_URL must be a string runtime setting` before truthiness checks, URL parsing, SSRF validation, sensitive-query validation, or production error aggregation. This prevents malformed direct runtime objects from executing URL hooks while startup validates outbound alert delivery configuration.

Direct worker alert emitters validate `RuntimeSettings.alert_webhook_url` and `RuntimeSettings.alert_webhook_max_body_bytes` before alert payload construction or transport use. `_emit_worker_failure_alert()` and `_emit_stale_requeue_alert()` reject URL string subclasses, malformed alert webhook URLs, non-integer body-size settings, non-positive body-size settings, and body-size settings above `65536` with RuntimeConfigError diagnostics that name the runtime setting. This keeps embedded worker callers aligned with startup validation instead of relying on lower-level `AlertDeliveryError` or URL helper exceptions after alert objects have already been rendered.

Production startup caps `JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS<=30`, so worker loops cannot be stalled
by multi-minute outbound waits during alert delivery.

Rejected-job alert delivery failures also use the shared safe exception diagnostic helper. If alert
exception stringification fails, lifecycle ingress logs `lifecycle raised unstringifiable <ExceptionType>`
or `lifecycle raised unstringifiable exception` instead of letting alert logging disrupt lifecycle
webhook acceptance.

Alert body text fields are bounded before JSON serialization. The delivery primitive rejects any generated `severity`, `status`, `summary`, `detail`, or `operator_action` value longer than 16 KiB before calling the JSON encoder or transport, so pathological alert diagnostics cannot force oversized serialization work before the existing `JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES` payload gate runs. The rejection diagnostic names only the field and configured limit, not the generated value.

`emit_alert_webhook()` rejects invalid direct body limits before URL validation, alert serialization, or transport use. Embedded callers cannot pass zero, negative, boolean, or non-integer `JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES` shaped values and continue into outbound alert delivery; invalid direct controls fail with `alert webhook max body bytes must be a positive integer`.

`emit_alert_webhook()` requires exact `HttpResponse` transport results before response status or body
inspection. Alert transports cannot return arbitrary response-shaped objects or response subclasses
that execute custom attribute hooks; malformed transport responses fail with
`alert webhook transport returned invalid response`.
`emit_alert_webhook()` wraps transport execution failures with `alert webhook transport request failed`
without stringifying or chaining the original exception. Malformed local alert transports cannot leak
credential-bearing request, proxy, DNS, TLS, socket, or adapter exception text through worker alert
failure diagnostics.

Alert routing fields use a fixed taxonomy before delivery. `severity` must be one of `critical`, `warning`, or `info`, and `status` must be one of `failed`, `rejected`, or `stale_requeued`. Unknown routing values are rejected before JSON serialization or transport, and rejection diagnostics name only the unsupported field, not the supplied value. This keeps downstream alert receivers from treating generated free-form text as routing policy.

Alert timestamps must be timezone-aware before delivery. The delivery primitive rejects naive `created_at` values before JSON serialization or transport so downstream incident timelines, audit storage, and replay diagnostics do not receive ambiguous local-time alert records.

Generated alert constructors also reject naive source timestamps before returning an `ExternalAlert`. Worker-failure alerts require timezone-aware `created_at` values, rejected-job alerts require timezone-aware job `updated_at` values, and stale-requeue alerts require timezone-aware `requeued_at` values. This keeps generated alert ids, incident timelines, and audit replay metadata from depending on ambiguous local server time.

Alert webhook outbound JSON is strict. `_alert_body_bytes()` preflights the Python-mode alert
payload with strict JSON numeric handling before compact JSON body generation. If a corrupted
in-process alert object contains `NaN`, `Infinity`, or `-Infinity`, body construction fails with
`alert webhook payload contains non-finite numeric values` before transport. The diagnostic does not
echo alert field names, story or correlation identifiers, or values, and Pydantic serializer warnings are suppressed so malformed alert shape is not leaked to logs. Unsupported non-JSON alert payload
values fail with `alert webhook payload contains non-JSON values`; alert webhook body generation
does not call `str()` or `repr()` on unsupported objects, bytes, or custom scalar values before
transport. Alert webhook payload keys and text values must be exact strings; string subclasses fail
with the same non-JSON diagnostic before compact JSON body generation or transport.
Alert payload traversal accepts only exact dictionaries, lists, and tuples; dictionary, list, and
tuple subclasses fail before `items()`, iteration, compact JSON body generation, or transport.

Alert webhook payload diagnostics do not retain unsafe causes. Malformed in-process alert payloads
still fail with `alert webhook payload contains non-finite numeric values` or
`alert webhook payload contains non-JSON values`, but those public `AlertDeliveryError` instances do
not chain lower-level Pydantic, validation, or JSON encoder exceptions. Crash reporters, traceback
formatters, worker warnings, and alert delivery logs therefore cannot re-expose alert field names,
story or correlation identifiers, credential-like fragments, object type names, or malformed values
through `__cause__`.

Alert sink response strings are size-capped after redaction before they are embedded in
`AlertDeliveryError` diagnostics. Oversized redacted strings are truncated with `...[truncated]`, so
a failed external alert sink cannot create oversized worker warnings or operator error messages even
when the sink returns a large JSON error body.

The full alert sink response diagnostic is also size-capped after recursive redaction. A response
with many ordinary structured entries is serialized in a deterministic compact form and truncated
with `...[truncated]` before being placed in `AlertDeliveryError`, so aggregate JSON response shape
cannot bypass the per-string diagnostic cap.

Alert sink response diagnostic traversal is bounded before serialization. Large exact response objects,
exact arrays, and exact tuples are sampled up to the alert response collection-item cap and include
`omitted_fields` or `omitted_items` markers. Dictionary, list, and tuple subclasses render as `[non-json value]` before `items()`, `len()`, iteration, or subclass hooks can execute. This keeps a failed alert sink from forcing the runtime
to recursively redact every nested entry just to produce a capped diagnostic.

Alert sink response dictionary truncation markers are collision-safe. If a sink response already
contains `__jedi_response_truncated__`, the original response field remains visible and the internal
truncation marker receives a deterministic duplicate suffix.

Alert sink response diagnostic traversal is cycle-safe. If an alternate transport or malformed sink payload supplies a cyclic exact dictionary, exact list, or exact tuple, the repeated active container renders as `[circular reference]` instead of raising a secondary recursion failure while formatting `AlertDeliveryError`.

Alert sink response diagnostic traversal is also depth-bounded. Deeply nested exact dictionaries, exact lists, and exact tuples are projected only to the alert response diagnostic depth cap; deeper containers render as `[max depth exceeded]` so malformed acyclic sink responses cannot consume unbounded recursive work before an alert failure is reported.

Alert sink response diagnostic keys are sanitized before JSON serialization. Response keys are
treated as untrusted sink output: secret-like key text is redacted, whitespace/control characters
are collapsed, oversized keys are capped, non-string keys become `[non-string key]`, and duplicate
sanitized labels receive deterministic duplicate suffixes instead of overwriting diagnostic values.
Only exact string keys and values enter alert sink response text redaction; string subclasses render
as `[non-string key]` for keys or `[non-json value]` for values instead of using subclass string
methods, object conversion, or custom behavior in diagnostics.

Alert sink response diagnostics are JSON-safe even if a transport supplies non-JSON nested values. Finite JSON scalar values are preserved after redaction, but non-finite floats, bytes, and arbitrary Python objects are represented by `[non-json value]` instead of type names, `repr()`, or string conversion. This replaces the earlier `non_json_type` marker and keeps binary payloads and object internals out of `AlertDeliveryError` diagnostics, along with custom transport implementation details.
Alert sink response boolean and integer values must be exact JSON scalar types; boolean and integer subclasses render as `[non-json value]` instead of being preserved as ordinary response numbers or booleans.

Every alert webhook request includes stable metadata headers for downstream deduplication and correlation:

```text
Idempotency-Key: <alert_id>
X-JEDI-Alert-ID: <alert_id>
X-JEDI-Job-ID: <job_id>
X-JEDI-Event-ID: <event_id>
X-JEDI-Story-Number: <story_number>
X-JEDI-Correlation-ID: <correlation_id, only when present>
```

Downstream alert receivers should treat `Idempotency-Key` as the dedupe key for retry-safe incident creation. The same values remain present in the JSON body for audit storage.

Alert header values are validated before sending. Any generated `alert_id`, `job_id`, `event_id`, story number, or correlation id containing ASCII control characters or exceeding 256 characters is rejected before transport invocation to prevent header injection and oversized metadata propagation. Empty or padded alert metadata values are also rejected before transport invocation to prevent blank idempotency keys and ambiguous correlation metadata. This fails the alert delivery attempt without mutating authoritative PostgreSQL job state.

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

The console shows Operational Alerts, recent fulfillment jobs, recent lifecycle events, and Basic-auth artifact detail pages under `/admin/artifacts/{artifact_id}`. It does not expose raw lifecycle event payload JSON or ServiceNow sys_ids in the dashboard. It also does not provide retry, reject, rebuild, preview, commit, or other mutation actions; ServiceNow remains the work surface and update set preview/commit remains the human review point.

`dev_basic` is development-only. The default `JEDI_ADMIN_AUTH_MODE=disabled` fails closed, and the runtime rejects `dev_basic` unless `JEDI_ENVIRONMENT=development`. Reserved production modes are `oidc` and `servicenow_oauth`; both fail closed until implemented. See `docs/admin-auth-config.md` for the required OIDC and ServiceNow OAuth configuration details.

Development Basic-auth console credentials are validated during runtime settings loading.
`JEDI_ADMIN_CONSOLE_USERNAME` and `JEDI_ADMIN_CONSOLE_PASSWORD` must be unpadded and free
of control characters before settings are returned, so accidental whitespace, tabbed
credential fragments, or log-injection characters cannot enter constant-time credential
comparison. Blank or absent values remain unconfigured and keep the admin console
fail-closed. The admin console authentication boundary also validates configured console credentials before parsing inbound Basic-auth payloads. If direct
`RuntimeSettings` construction or a future alternate settings loader bypasses normal
settings validation, non-ASCII, padded, control-character-bearing, or larger-than-8192-byte
configured console username/password values fail closed as invalid runtime configuration
with `503` before inbound Basic auth is decoded or compared.

## Fulfillment Worker

The worker boundary is `process_one_fulfillment_job()` in `jedi_devproject.fulfillment_worker`. It claims one queued job from PostgreSQL with `claim_next_fulfillment_job(worker_id=...)`, calls an injected fulfillment handler, and records the terminal job state.

Successful handlers call `complete_fulfillment_job()` and append a `completed` job event. Handler failures call `fail_fulfillment_job()`, store the error in `last_error`, clear the worker lock, and append a `failed` job event.

The first production handler is `build_claim_fulfillment_handler()` in `jedi_devproject.fulfillment_handler`. It converts a claimed fulfillment job into an `execute_build_claim()` request, using the job story number and lifecycle event id to move the story from `Ready` to `Work in Progress` through the existing guarded writeback path.

Intake feedback story lookup is exact-shape guarded inside the fulfillment handler's fail-open feedback path. `_assess_intake_feedback()` accepts only exact Python lists containing exact `Story` records from `fetch_stories()`. List subclasses, alternate iterables, model subclasses, and malformed entries fail with `intake story fetch contains non-JSON value` before truthiness hooks, indexing hooks, enrichment `model_copy()` hooks, capability analysis, work-note planning, ServiceNow mutation, or feedback artifact writing can execute caller-controlled behavior. Because intake feedback is intentionally fail-open, malformed intake story fetches are logged as sanitized fixed diagnostics and do not block the already-claimed build path.

The worker runs outside the webhook request. The webhook should only validate, record, enqueue, and acknowledge lifecycle events.

The long-running worker also owns optional periodic maintenance such as retention pruning and stale running job recovery. Maintenance failures are isolated from fulfillment processing: a failed prune or stale recovery pass logs a warning with diagnostic redaction, increments `prune_failures` or `stale_job_recovery_failures` in the worker loop summary, and the worker still attempts the normal fulfillment iteration. Maintenance failure handling does not mutate PostgreSQL job state unless the underlying maintenance operation completed its own transaction.
Runtime-worker maintenance and alert logging also tolerates malformed exception objects. Retention
prune failures, stale-job recovery failures, stale-requeue alert delivery failures, and worker
failure-alert delivery failures are formatted through a safe diagnostic helper before logging. If
exception stringification fails, the worker logs `runtime worker raised unstringifiable <ExceptionType>`
or the generic `runtime worker raised unstringifiable exception`, increments the appropriate failure
counter, and continues the loop according to the configured stop policy.

## Runtime Wiring

Runtime configuration is loaded by `load_runtime_settings()` in `jedi_devproject.runtime`. Required environment values are:

- `DATABASE_URL`
- `SERVICENOW_PM_INSTANCE_URL`, `SERVICENOW_PM_CLIENT_ID`, and `SERVICENOW_PM_CLIENT_SECRET` for the story/source instance.
- `SERVICENOW_DEV_INSTANCE_URL`, `SERVICENOW_DEV_CLIENT_ID`, and `SERVICENOW_DEV_CLIENT_SECRET` for the development target instance.
- `JEDI_AUDIT_ROOT`

The legacy `SERVICENOW_INSTANCE_URL`, `SERVICENOW_CLIENT_ID`, and `SERVICENOW_CLIENT_SECRET` values remain as a single-instance fallback for local tests and old deployments. New runtime deployments should use the PM/DEV split. Story retrieval, story state choices, story dictionary checks, story status updates, and failure work notes use the PM client. Live table/form context retrieval, platform metadata reads, bootstrap-style platform writes, and retrieved Update Set imports use the DEV client.

Runtime settings loading rejects padded or control-character ServiceNow OAuth credential
values before settings are returned. The split runtime keys `SERVICENOW_PM_CLIENT_ID`,
`SERVICENOW_PM_CLIENT_SECRET`, `SERVICENOW_DEV_CLIENT_ID`, and
`SERVICENOW_DEV_CLIENT_SECRET` must be unpadded and free of control characters, and the
legacy single-instance fallback is validated after it is resolved into PM/DEV credential
settings. Malformed credential diagnostics name only the resolved setting and do not echo
credential fragments.

Runtime settings loading also rejects blank split ServiceNow overrides before fallback
resolution. If any of `SERVICENOW_PM_INSTANCE_URL`, `SERVICENOW_PM_CLIENT_ID`,
`SERVICENOW_PM_CLIENT_SECRET`, `SERVICENOW_DEV_INSTANCE_URL`,
`SERVICENOW_DEV_CLIENT_ID`, or `SERVICENOW_DEV_CLIENT_SECRET` is present, it must be a
real value; remove the split key entirely to use the legacy single-instance fallback.
This prevents whitespace-only or empty PM/DEV settings from silently routing stories or
development writes to the wrong instance.

Split ServiceNow fallback resolution is exact-string guarded. `_env_value()` and
`_blank_split_servicenow_override_errors()` reject string subclasses and non-string objects with
`<SETTING> must be a string runtime setting` before truthiness checks, fallback selection,
`.strip()`, URL validation, OAuth credential validation, or runtime settings construction. This keeps
malformed in-process configuration maps from executing caller-controlled hooks while deciding which
PM or DEV ServiceNow instance receives reads and writes.

Optional values are documented in `.env.example`, the synchronized production operator template, and must stay synchronized with `load_runtime_settings()`.
The template includes runtime role controls, worker
identity, build-claim state controls, update-set apply controls, classifier
gating, model-provider settings, admin authentication, lifecycle webhook
authentication, rate limits, request body ceilings, HSTS, stale-job recovery,
alert delivery, and public-document retrieval controls. Production operators
should start from `.env.example`, fill required secrets in the deployment
secret store, and deliberately remove or leave blank disabled features instead
of relying on undocumented runtime defaults. The API process should call
`create_runtime_api()` with these settings. The worker process should call
`process_one_runtime_fulfillment()` in a loop or scheduler owned by the runtime
host.

Runtime boolean environment values are strict. `JEDI_BUILD_CLAIM_APPLY`, `JEDI_STRICT_TRANSPORT_SECURITY_ENABLED`, `JEDI_ALERT_WEBHOOK_ENABLED`, `JEDI_UPDATE_SET_APPLY`, and `JEDI_CLASSIFIER_GATE` accept only `true`, `false`, `1`, `0`, `yes`, `no`, `on`, or `off`, case-insensitively and without padding or control characters. Malformed values fail settings loading instead of being silently treated as false; diagnostics include the setting name and do not silently normalize operator input.

Runtime numeric environment values are strict. Integer settings such as request body sizes, rate-limit counts, rate-limit windows, stale-job thresholds, HSTS max age, alert webhook max body bytes, and public-web byte/result limits must parse as ASCII base-10 digits only without signs, underscores, padding, or control characters. Timeout settings such as `JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS` and `JEDI_PUBLIC_WEB_TIMEOUT_SECONDS` must parse as finite numbers without padding or control characters, and the accepted token format is now fixed ASCII decimal numbers without signs, underscores, or exponent notation. This rejects exponent notation, padding, or control characters instead of silently normalizing operator input; non-finite values such as `nan`, `inf`, and `-inf` are rejected. Malformed numeric values fail settings loading with the setting name instead of surfacing raw parser errors or silently normalizing operator input. Runtime numeric parser error wrapping also uses the shared safe exception diagnostic helper, so malformed parser exception objects fail as `runtime config raised unstringifiable <ExceptionType>` or `runtime config raised unstringifiable exception` instead of letting secondary stringification errors leak configuration-adjacent text.

Runtime boolean, enum, and environment-mode settings require exact strings or `None` before parsing.
`_bool_value()`, `_enum_value()`, and `_runtime_environment_value()` use a shared exact-string
runtime setting reader, so string subclasses and non-string objects fail with `<SETTING> must be a
string runtime setting` before truthiness checks, `str()` conversion, padding checks, enum matching,
or mode normalization. This keeps malformed in-process configuration maps from executing
caller-controlled hooks or leaking object type names while loading production runtime settings.

Optional runtime settings are exact-string guarded before optional blank handling or secondary
validation. `JEDI_MODEL_PROVIDER`, `JEDI_ALERT_WEBHOOK_URL`, `JEDI_ADMIN_USERNAME`,
`JEDI_ADMIN_PASSWORD`, `OPENAI_API_KEY`, `OPENAI_MODEL`, and shared optional unpadded runtime
controls reject string subclasses and non-string objects with `<SETTING> must be a string runtime
setting` before `.strip()`, equality checks, URL validation, provider validation, admin credential
byte-length checks, or runtime settings construction. This prevents malformed in-process
configuration maps from executing optional-setting hooks or leaking object type names while startup
parses optional production controls.

Runtime settings loading validates the required store and audit boundary before
settings are returned. `DATABASE_URL` must be a PostgreSQL URL without raw
whitespace/control characters, encoded whitespace/control characters, or URL
fragments. `JEDI_AUDIT_ROOT` must be an absolute path without whitespace or
control characters. Malformed diagnostics name only `DATABASE_URL` or
`JEDI_AUDIT_ROOT` and do not echo database credentials or path fragments.
Required store and audit values are exact-string guarded before validation. `DATABASE_URL` and
`JEDI_AUDIT_ROOT` values from merged runtime configuration fail with `<SETTING> must be a string
runtime setting` when they are string subclasses or non-string objects, before URL parsing,
`Path(...)` construction, Pydantic settings construction, or startup validation. This prevents
malformed in-process dotenv/config maps from executing conversion hooks or carrying database
credential fragments into diagnostics.
Direct `RuntimeSettings.database_url` validation is exact-string guarded before production database URL hygiene checks. `validate_runtime_settings()` rejects database URL string subclasses or non-string objects with `DATABASE_URL must be a string runtime setting` before URL parsing, whitespace/control-character scans, encoded-control scans, scheme checks, fragment checks, hostname checks, or production error aggregation. This prevents malformed direct runtime objects from reaching lower-level URL parsers while startup validates the PostgreSQL operational store boundary.
Direct `RuntimeSettings.audit_root` validation is exact concrete-path guarded before production audit-root hygiene checks. `validate_runtime_settings()` rejects non-path objects or path subclasses with `JEDI_AUDIT_ROOT must be a path runtime setting` before `str()`, `is_absolute()`, whitespace/control-character scans, or production error aggregation. This prevents malformed direct runtime objects from executing path conversion hooks while startup validates local audit evidence storage.

Direct `RuntimeSettings` construction also suppresses rejected input values in
Pydantic validation errors. Type, enum, and parsing failures still name the
invalid field, but they do not echo rejected database URL values,
admin/public-web selector text, numeric setting fragments, or other raw
configuration input into startup logs, worker failures, artifacts, or
ServiceNow work notes.

`JEDI_ENVIRONMENT` is a strict runtime mode switch, not free-form deployment metadata. It accepts only `development` or `production`, case-insensitively, and settings loading stores the normalized lowercase value. Non-empty values with leading, trailing, or internal whitespace/control characters are rejected instead of silently trimmed. Malformed values such as `prod` fail settings loading with `JEDI_ENVIRONMENT` in the error so production startup validation cannot be bypassed by a misspelled environment name.

Direct `RuntimeSettings.runtime_environment` wiring follows the same boundary. `validate_runtime_settings()` rejects malformed direct runtime environment values before deciding whether production checks apply, so a malformed value cannot silently downgrade a production runtime into development behavior.
Direct runtime mode and role validation is exact-string guarded as well.
`validate_runtime_settings()` rejects direct `RuntimeSettings.runtime_environment` and
`RuntimeSettings.runtime_role` string subclasses or non-string objects with `<SETTING> must be a
string runtime setting` before `.strip()`, `str()` conversion, production/development branching,
runtime role routing, or role-specific production checks. This prevents malformed direct
`RuntimeSettings` objects from executing caller-controlled hooks while deciding whether production
security controls apply.
Runtime role validation runs before development-mode startup exits and before worker fulfillment rejects API-only runtime roles. `validate_runtime_settings()` now exact-string validates direct `RuntimeSettings.runtime_role` values even when `JEDI_ENVIRONMENT=development`, and `process_one_runtime_fulfillment()` calls that validation before checking whether the role is `api`. This keeps direct worker entrypoints from executing malformed runtime-role equality hooks before startup validation.
Production runtime role-policy helpers consume normalized values only. The API-role and worker-role checks no longer read raw `RuntimeSettings` attributes for worker-only provider settings, API-only webhook/admin settings, or development-only admin console credentials after `validate_runtime_settings()` has already performed exact-type normalization. This keeps role-policy decisions downstream of the shared runtime setting boundary and reduces the chance that future role checks bypass direct-object hardening.
Direct production credential validation follows the same exact-string boundary.
`validate_runtime_settings()` rejects direct `RuntimeSettings.lifecycle_webhook_secret` and
`RuntimeSettings.admin_api_token` string subclasses or non-string objects with `<SETTING> must be a
string runtime setting` before truthiness checks, `len()`, credential byte-length checks, ASCII
checks, whitespace/control-character scans, admin-auth requirement checks, or production error
aggregation. This prevents malformed direct `RuntimeSettings` objects from executing credential
hooks or leaking credential-like fragments while production startup validates webhook and admin
authentication controls.
Direct auth-mode validation is exact-string guarded before production security decisions.
`validate_runtime_settings()` rejects direct `RuntimeSettings.lifecycle_webhook_auth_mode` and
`RuntimeSettings.admin_auth_mode` string subclasses or non-string objects with `<SETTING> must be a
string runtime setting` before equality checks, `str()` conversion, whitespace/control-character
scans, allowed-mode checks, admin-auth requirement checks, or unimplemented-auth diagnostics. This
prevents malformed direct `RuntimeSettings` objects from executing auth-mode hooks while production
startup validates webhook and admin authentication posture.
Direct model-provider validation is exact-string guarded before worker model routing.
`validate_runtime_settings()` rejects direct `RuntimeSettings.model_provider`,
`RuntimeSettings.openai_api_key`, and `RuntimeSettings.openai_model` string subclasses or non-string
objects with `<SETTING> must be a string runtime setting` before truthiness checks, `len()`,
model-provider length checks, provider equality checks, OpenAI-required-field checks, or
whitespace/control-character scans. This prevents malformed direct `RuntimeSettings` objects from
executing model credential hooks while production startup validates model fulfillment controls.
Runtime fulfillment handler assembly uses the same exact-string boundary before constructing model providers
or public documentation retrievers. `_runtime_handler()` rejects malformed direct
`RuntimeSettings.model_provider`, `RuntimeSettings.openai_api_key`, `RuntimeSettings.openai_model`,
and `RuntimeSettings.public_web_access` values with `RuntimeConfigError` before model-provider
length checks, provider equality checks, OpenAI settings construction, public-web equality checks,
handler composition, or claim-handler execution.
Direct public-web access validation is exact-string guarded before public documentation routing.
`validate_runtime_settings()` rejects direct `RuntimeSettings.public_web_access` string subclasses or
non-string objects with `JEDI_PUBLIC_WEB_ACCESS must be a string runtime setting` before equality
checks, API-role worker-only checks, required allowlist checks, required documentation URL checks, or
public-documentation allowlist validation. This prevents malformed direct `RuntimeSettings` objects
from executing selector hooks while production startup decides whether worker public web retrieval is
enabled.

Runtime enum environment values are strict. `JEDI_ADMIN_AUTH_MODE` accepts only `disabled`, `dev_basic`, `oidc`, or `servicenow_oauth`; `JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE` accepts only `disabled`, `shared_secret`, `hmac_sha256`, or `servicenow_oauth`; and `JEDI_PUBLIC_WEB_ACCESS` accepts only `disabled` or `worker`. Non-empty enum values with leading, trailing, or internal whitespace/control characters are rejected instead of silently trimmed. Malformed enum values fail settings loading with the setting name and allowed values instead of surfacing raw model validation errors.

`JEDI_WORKER_ID` is stored in PostgreSQL lock and job-event metadata. Runtime settings loading rejects empty, padded, or control-character worker ids before they can enter worker settings, and production startup validation applies the same boundary to direct `RuntimeSettings` wiring so `locked_by` and operational audit evidence remain printable and unambiguous.
Direct `RuntimeSettings.worker_id` validation is exact-string guarded before production worker-id hygiene checks. `validate_runtime_settings()` rejects worker id string subclasses or non-string objects with `JEDI_WORKER_ID must be a string runtime setting` before truthiness checks, `.strip()`, control-character scans, or production error aggregation. This prevents malformed direct runtime objects from executing worker-id hooks while startup validates lock owner and job-event audit metadata.

`JEDI_CLASSIFIER_GATE` defaults to `true`. When `true`, the worker keeps the normal fail-closed classifier gate: unknown or unsupported story surfaces do not call the model and receive human-review feedback. Setting `JEDI_CLASSIFIER_GATE=false` is an experimental development control that lets unknown classifier outcomes call the model for exploratory structured reasoning. It is rejected in production startup validation and must only be used in development. It does not enable automatic retrieved Update Set handoff for those stories; non-automated classifier outcomes remain `Human Review Required`.

For ServiceNow Table API integrations, prefer state values over labels. In the current PDI, `Ready` is `1` and `Work in progress` is `2`, so the Railway worker uses `JEDI_BUILD_CLAIM_FROM_STATE=1` and `JEDI_BUILD_CLAIM_STATE=2`. Runtime settings loading rejects empty, padded, or control-character build claim state values before they can enter worker settings. When `JEDI_BUILD_CLAIM_APPLY=true` in production, startup validation rejects empty, padded, or control-character build claim state values before the worker can write an ambiguous ServiceNow transition; startup validation also rejects malformed direct build claim state values.
Direct `RuntimeSettings.build_claim_from_state` and `RuntimeSettings.build_claim_state` validation is exact-string guarded before production build-claim hygiene checks. `validate_runtime_settings()` rejects build-claim state string subclasses or non-string objects with `JEDI_BUILD_CLAIM_FROM_STATE must be a string runtime setting` or `JEDI_BUILD_CLAIM_STATE must be a string runtime setting` before truthiness checks, `.strip()`, control-character scans, or production error aggregation. This prevents malformed direct runtime objects from executing state-value hooks while startup validates the ServiceNow claim transition metadata.

`runtime_worker.run_loop()` provides the built-in polling loop for hosts that run the worker as a long-lived process. It repeatedly calls the same one-job runtime processor, sleeps after idle polls, and can stop on the first failed job for smoke tests or continue when the host owns failure alerting.

Runtime fulfillment failures write back to the originating ServiceNow story work notes through the worker `failure_notifier`. The note begins with `Automated fulfillment failed` and includes the lifecycle event id, fulfillment job id, and redacted failure message. Each interpolated value is treated as untrusted: lifecycle event ids, job ids, and failure messages are redacted, whitespace/control characters are collapsed, and each value is capped at 500 characters including the truncation marker before being appended to the ServiceNow work note. If the ServiceNow writeback itself fails, the worker still marks the PostgreSQL job failed and stores both the original handler error and the notifier error in `last_error`.
`_servicenow_failure_notifier()` sanitizes the story number before raising the `story not found` diagnostic. Lookup-miss diagnostics redact secret-like fragments, collapse whitespace/control characters, apply configured literal-secret redaction, and enforce the same 500-character work-note value ceiling before the notifier error is appended to worker failure diagnostics.
`_servicenow_failure_notifier()` validates story lookup query parts before calling `fetch_stories()`. The failure notifier rejects empty, non-string, oversized, control-character-bearing, or encoded-query delimiter-bearing `story_sys_id` and `story_number` values with the fixed `story lookup query is unsafe` diagnostic before ServiceNow lookup, OAuth acquisition, work-note writeback, or query construction.
`_servicenow_failure_notifier()` applies record-id syntax validation to `story_sys_id` lookup values. Authoritative sys-id lookup values must be exact, unpadded strings of letters, digits, underscores, and hyphens within the lookup-part ceiling; malformed sys ids fail with `story lookup query is unsafe` before encoded-query construction or ServiceNow lookup.
`_servicenow_failure_notifier()` validates story lookup collection shape before story-not-found handling or failed-story mutation. `fetch_stories()` must return an exact Python list; list subclasses, tuples, alternate iterables, and malformed collection objects fail with `story lookup result is unsafe` before truthiness hooks, indexing hooks, Draft-state lookup, ServiceNow mutation, or failure work-note construction can execute caller-controlled behavior.
`_servicenow_failure_notifier()` validates found story `sys_id` values before failed-story update. Returned story identifiers must pass the same exact-string record-id syntax guard before `update_story_fields()` is called, so malformed lookup results cannot redirect failed-story state or work-note writes.
`SplitServiceNowClient` validates PM/story lookup collection shape before returning data to runtime workers or CLI orchestration. `fetch_ready_stories()` and `fetch_stories()` must return exact Python lists from the configured PM/story client; list subclasses, tuples, alternate iterables, and malformed collection objects fail with `story lookup result is unsafe` before downstream truthiness hooks, length hooks, worker scheduling, pipeline execution, or development-instance operations can consume caller-controlled collection behavior.
`SplitServiceNowClient` validates PM story metadata collection shape too. `fetch_story_state_choices()` must return an exact Python list or fail with `story state choices result is unsafe`, and `fetch_story_dictionary_fields()` must return an exact Python list or fail with `story dictionary fields result is unsafe`. These checks run before downstream truthiness hooks, length hooks, state-choice iteration, dictionary-field iteration, writeback state mapping, bootstrap checks, or story metadata decisions can consume caller-controlled collection behavior.
`SplitServiceNowClient` validates PM story mutation response shape before returning update results to notifiers, writeback callers, or CLI orchestration. `update_story_fields()` returns only an exact Python dictionary, otherwise it fails with `story mutation result is unsafe` before downstream truthiness hooks, length hooks, response-field reads, audit decisions, or notifier completion logic can consume caller-controlled response behavior.
`SplitServiceNowClient` also validates development table-record collection shape before returning data to builders, discovery routines, or update-set handoff logic. `fetch_table_records()` must return an exact Python list from the configured development client; list subclasses, tuples, alternate iterables, and malformed collection objects fail with `table record lookup result is unsafe` before downstream truthiness hooks, length hooks, table-record iteration, builder routing, update-set XML generation, or development-instance mutations can consume caller-controlled collection behavior.
`SplitServiceNowClient` validates development single-record and mutation response shapes before returning them to runtime callers. `fetch_table_record()` returns only `None` or an exact Python dictionary, otherwise it fails with `table record lookup result is unsafe`. `upsert_table_record()` returns only an exact Python dictionary, otherwise it fails with `table mutation result is unsafe`. `import_update_set_xml()` returns only an exact Python dictionary, otherwise it fails with `update set import result is unsafe`. These checks run before downstream truthiness hooks, length hooks, record-field reads, mutation-result reads, handoff decisions, or import-status decisions can consume caller-controlled response behavior.
`_story_state_choice_value()` skips malformed state-choice records before comparing labels. Failure-notifier Draft-state discovery accepts only exact-string state-choice labels and values from the ServiceNow client, and malformed records are ignored without stringification so secondary state-choice metadata defects cannot replace failed-story work-note writeback.
`_story_state_choice_value()` rejects unsafe exact-string state-choice values before returning the state. State-choice labels and values must be exact, unpadded strings without ASCII control characters and within the metadata text ceiling; unsafe records are skipped so malformed Draft-state metadata cannot be written back as the story state.

Runtime completion closeout also writes a ServiceNow work note when a `Ready for Testing` to `Complete` lifecycle event closes the loop. The completion lifecycle event id is redacted, whitespace/control characters are collapsed, and capped at 500 characters including the truncation marker before it is appended to the human-readable closeout note.
`_servicenow_complete_notifier()` sanitizes the story number before raising the missing `story_sys_id` diagnostic. Missing-sys-id completion diagnostics redact secret-like fragments, collapse whitespace/control characters, and apply the same 500-character work-note value ceiling before the runtime error is exposed to lifecycle API logs or operator diagnostics.
`_servicenow_complete_notifier()` validates completion `story_sys_id` values before closeout update. Completion record ids must be exact, unpadded strings of letters, digits, underscores, and hyphens within the runtime record-id ceiling; malformed completion ids fail with `completed story_sys_id is unsafe` before `update_story_fields()` is called.

Worker failure diagnostics are redacted at the core fulfillment-worker boundary before notifier delivery, PostgreSQL persistence, and `FulfillmentWorkerResult` return. Handler errors and notifier errors preserve non-sensitive reason text, but diagnostic redaction removes URL credentials, sensitive query parameters such as `client_secret`, Authorization header values, cookie values, private-key blocks, and sensitive assignment values such as `api_key`. This applies even when callers use `process_one_fulfillment_job()` directly instead of the runtime wrapper.
Shared diagnostic redaction through `_redact_diagnostic_text()` accepts only exact strings or `None`. Direct non-string inputs and
string subclasses render as `[non-string diagnostic text]` before URL parsing, regex replacement,
query-key decoding, or assignment redaction can run. This keeps alerts, work notes, provider
diagnostics, and ServiceNow/API failure paths from executing caller-controlled string-subclass
behavior or surfacing raw regex/type errors.
The core worker also tolerates malformed handler and notifier exception objects. If exception
stringification fails while a job is being failed, the worker records a bounded generic
`worker raised unstringifiable <ExceptionType>` diagnostic, still calls the failure notifier when
applicable, still persists the failed job, and still returns a failed `FulfillmentWorkerResult`.
Unsafe, non-ASCII, oversized, or mutated exception type labels collapse to
`worker raised unstringifiable exception`.

Runtime handler redaction also tolerates malformed exception objects. If a fulfillment handler raises
an exception whose `__str__` method fails, the runtime wrapper stores and reports a generic
`handler raised unstringifiable <ExceptionType>` message instead of letting the secondary
stringification failure bypass redaction or leak credential text from the stringification error.
The exception type label is included only when it is an ASCII Python identifier no longer than 128
characters. Unsafe, non-ASCII, oversized, or mutated type labels collapse to
`handler raised unstringifiable exception`.

Runtime handler redaction diagnostics do not retain unsafe causes. Handler failures wrapped by `_redacting_handler()` still preserve fixed redacted messages such as `handler raised unstringifiable _UnstringifiableRuntimeError`, but the public `RuntimeError` does not chain the original handler exception. Worker logs, failed-job records, admin diagnostics, alert payloads, and crash reporters therefore cannot re-expose handler exception payloads, hostile stringification failures, credential-like fragments, or unsafe exception type state through `__cause__`.
`_redacting_handler()` treats literal `secret_values` as untrusted. Runtime literal secret entries are projected to a bounded exact-string set before replacement; non-string values, string subclasses, empty values, oversized values, and hostile iterators are ignored or fail closed without replacing the original handler failure with a secret-iterator diagnostic.
`_servicenow_failure_notifier()` passes untrusted `secret_values` directly into hardened sanitizers after first projecting them through the same bounded exact-string literal secret policy. Hostile iterators, non-string entries, string subclasses, empty values, and oversized values therefore cannot crash failed-job work-note construction or replace the original fulfillment failure with a secret-iterator diagnostic.

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

- Lifecycle webhook bodies over `JEDI_LIFECYCLE_WEBHOOK_MAX_BODY_BYTES` are rejected with `413`; the receiver enforces this while streaming the request body, before JSON parsing, HMAC validation, lifecycle planning, or operational-store writes.
- Lifecycle webhook bursts over `JEDI_LIFECYCLE_RATE_LIMIT_MAX_REQUESTS` within `JEDI_LIFECYCLE_RATE_LIMIT_WINDOW_SECONDS` are rejected with `429`; lifecycle limiter state uses `JEDI_LIFECYCLE_RATE_LIMIT_MAX_BUCKETS` to cap live bucket cardinality.
- Admin diagnostic request bodies over `JEDI_ADMIN_MAX_BODY_BYTES` are rejected with `413` before
  auth, artifact, job, or list handlers query the operational store. The middleware validates
  both declared `Content-Length` and the actual streamed body, so missing or misleading length
  headers do not bypass the cap.
- Admin JSON endpoints use `JEDI_ADMIN_RATE_LIMIT_MAX_REQUESTS` and `JEDI_ADMIN_RATE_LIMIT_WINDOW_SECONDS` and return `429` when exceeded; admin limiter state uses `JEDI_ADMIN_RATE_LIMIT_MAX_BUCKETS` to cap live bucket cardinality.
- Admin list endpoints cap requested limits at 100 rows even when callers request a larger value.

Production startup also caps configured body-size limits: `JEDI_LIFECYCLE_WEBHOOK_MAX_BODY_BYTES<=1048576`, `JEDI_ADMIN_MAX_BODY_BYTES<=65536`, and `JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES<=65536`. Defaults are intentionally conservative for the PDI/Railway MVP: lifecycle webhooks allow 64 KiB bodies, admin diagnostic routes allow 8 KiB bodies, alert webhook egress allows 16 KiB bodies, lifecycle allows 60 calls per 60 seconds, admin allows 120 calls per 60 seconds, and both lifecycle and admin limiters allow 10000 live buckets per process. These controls are a per-process MVP control. They are not a distributed Federal production abuse-control boundary. Production should also enforce request size, request rate, IP reputation, and alerting at an edge, WAF, or API gateway layer approved by the customer environment.

Production API and combined roles must set `JEDI_TRUSTED_HOSTS` to a comma-separated list of allowed Host header values, for example `api.example.gov` or `*.apps.example.gov`. Runtime API construction installs Starlette `TrustedHostMiddleware` when the list is configured, and production startup rejects missing or malformed trusted-host values before serving traffic. Production values must be exact hostnames or wildcard subdomains without schemes, paths, padding, whitespace, control characters, local hosts, invalid ports, or wildcard-all entries. Development can leave the setting blank for local tooling, but public deployments must not rely only on the hosting provider to reject unexpected Host headers.

The runtime API construction rejects non-positive rate-limit settings instead of silently disabling limiters. Direct `RuntimeSettings` construction, tests, or future alternate settings loaders cannot set `JEDI_LIFECYCLE_RATE_LIMIT_MAX_REQUESTS`, `JEDI_LIFECYCLE_RATE_LIMIT_WINDOW_SECONDS`, `JEDI_LIFECYCLE_RATE_LIMIT_MAX_BUCKETS`, `JEDI_ADMIN_RATE_LIMIT_MAX_REQUESTS`, `JEDI_ADMIN_RATE_LIMIT_WINDOW_SECONDS`, or `JEDI_ADMIN_RATE_LIMIT_MAX_BUCKETS` to zero or a negative value and still start the API. Invalid runtime limiter construction fails closed with `RuntimeConfigError` naming the setting before lifecycle or admin routes serve traffic.

The runtime API construction rejects invalid alert webhook settings when alert delivery is enabled. Direct `RuntimeSettings` construction, tests, or future alternate settings loaders cannot start the API with non-positive or oversized `JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS` or `JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES`; invalid values fail closed with `RuntimeConfigError` naming the setting before alert transport creation, operational store opening, or route serving.

The runtime API construction rejects invalid request body limits before serving traffic. Direct `RuntimeSettings` construction, tests, or future alternate settings loaders cannot start the API with non-positive or oversized `JEDI_LIFECYCLE_WEBHOOK_MAX_BODY_BYTES` or `JEDI_ADMIN_MAX_BODY_BYTES`; invalid values fail closed with `RuntimeConfigError` naming the setting before lifecycle route creation, admin middleware use, operational store opening, or route serving.

### Production Runtime Fail-Closed Checklist

Production API and worker entrypoints call `validate_runtime_settings()` before opening the operational store or processing work. Development can run with local defaults, but `JEDI_ENVIRONMENT=production` fails closed unless the runtime posture is explicit.

Production requirements:

- `JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE=hmac_sha256`
- `JEDI_LIFECYCLE_WEBHOOK_SECRET=<shared signing secret>` with at least 32 characters
- `JEDI_LIFECYCLE_WEBHOOK_MAX_SKEW_SECONDS<=900` for public production roles
- `JEDI_LIFECYCLE_WEBHOOK_MAX_BODY_BYTES<=1048576`
- `JEDI_ADMIN_MAX_BODY_BYTES<=65536`
- `JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES<=65536`
- `JEDI_RUNNING_JOB_STALE_AFTER_SECONDS<=86400`
- `JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS<=30`
- `JEDI_PUBLIC_WEB_TIMEOUT_SECONDS<=30`
- `JEDI_MODEL_PROVIDER=openai`
- `OPENAI_API_KEY=<provider key>`
- `OPENAI_MODEL=<approved model id>`
- `JEDI_TRUSTED_HOSTS=<public API hostnames>` for `api` and `combined` production roles
- `JEDI_STRICT_TRANSPORT_SECURITY_ENABLED=true` for `api` and `combined` production roles
- `JEDI_STRICT_TRANSPORT_SECURITY_MAX_AGE_SECONDS>=31536000` for `api` and `combined` production
  roles
- `JEDI_ALLOW_COMBINED_PRODUCTION=true` only when a production deployment intentionally runs a
  single combined API and worker process
- `JEDI_ADMIN_API_TOKEN=<strong operator token>` when `JEDI_ADMIN_AUTH_MODE=disabled`

`JEDI_ADMIN_AUTH_MODE=disabled` is the supported interim production posture only when
`JEDI_ADMIN_API_TOKEN` is configured. In that mode, browser admin console routes stay unavailable
with `503`, while JSON admin diagnostics and artifact APIs require the bearer token. This keeps the
public API deployable without enabling a browser identity model before OIDC or ServiceNow OAuth is
implemented. `JEDI_ADMIN_AUTH_MODE=dev_basic` is rejected in production. Reserved production admin
modes `oidc` and `servicenow_oauth` remain fail-closed until their token validation, session
handling, and authorization checks are implemented. Public production roles also reject
`JEDI_ADMIN_CONSOLE_USERNAME` and `JEDI_ADMIN_CONSOLE_PASSWORD`; those Basic-auth credentials are
development-only and must not be deployed beside the bearer-only production posture.

Direct `RuntimeSettings.admin_auth_mode` wiring is validated during production startup as well as env loading. Malformed direct values are rejected with fixed `JEDI_ADMIN_AUTH_MODE` diagnostics and are not echoed into startup errors. The admin console fallback for unsupported direct auth modes also returns a fixed diagnostic rather than reflecting arbitrary auth-mode text.

Security-sensitive runtime auth decisions do not normalize runtime mode strings. The lifecycle webhook disabled-auth development exception and the development Basic-auth admin console both require the exact normalized value `development`; padded, whitespace-bearing, control-character-bearing, mixed-case, or otherwise malformed direct runtime environment values fail closed instead of being treated as development.

Production startup validation requires an absolute `JEDI_AUDIT_ROOT` path without whitespace or control characters. Although operational artifacts are DB-backed, legacy writeback and smoke paths can still write local audit artifacts, so hosted deployments must not depend on a relative working directory for audit evidence.

Production startup validation requires a PostgreSQL operational store. `DATABASE_URL` must use a PostgreSQL scheme and must not include URL fragments, raw or encoded whitespace or control characters. Deployment should fail before the API or worker opens state if a local file-backed, malformed, or ambiguous database URL is configured.

Runtime settings loading rejects padded or control-character `JEDI_LIFECYCLE_WEBHOOK_SECRET`
values before settings are returned, so lifecycle signing secrets cannot be silently normalized
or pass log-injection characters into webhook authentication paths. Blank or absent values remain
unconfigured and keep authenticated webhook modes fail-closed.

Production startup validation also rejects malformed HMAC webhook secrets. When `JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE=hmac_sha256`, `JEDI_LIFECYCLE_WEBHOOK_SECRET` must be at least 32 characters, must be at most 8192 bytes, and must not contain whitespace or control characters. Deployment should fail before the API accepts lifecycle events if an environment manager injects a newline, tab, or padded secret value, and it should also fail before serving if the configured secret is oversized. The startup validation and request-time lifecycle auth share one credential ceiling through `MAX_LIFECYCLE_WEBHOOK_CREDENTIAL_BYTES`, so configured webhook secrets cannot pass startup with a value the lifecycle receiver would later reject.

Lifecycle webhook signing supports an explicit rotation window through `JEDI_LIFECYCLE_WEBHOOK_PREVIOUS_SECRET`. In production, the previous secret uses the same length, byte-size, whitespace, and control-character rules as `JEDI_LIFECYCLE_WEBHOOK_SECRET`, and it must differ from the active secret. Startup rejects deployments where the previous secret equals the active secret. During rotation the API accepts HMAC signatures generated with either the active or previous secret, and it performs the configured-secret comparisons without disclosing which secret matched. The previous-secret setting is API-only and must not be present on worker-only services.

Use this lifecycle webhook secret rotation runbook for low-downtime production rotation:

1. Generate a new customer-approved webhook signing secret in the approved secret manager. Do not reuse the existing `JEDI_LIFECYCLE_WEBHOOK_SECRET`.
2. Move the currently deployed `JEDI_LIFECYCLE_WEBHOOK_SECRET` value into `JEDI_LIFECYCLE_WEBHOOK_PREVIOUS_SECRET`, set the new value as `JEDI_LIFECYCLE_WEBHOOK_SECRET`, and redeploy or restart the API service.
3. Verify API startup succeeds with `JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE=hmac_sha256` and no production validation diagnostics.
4. Update the ServiceNow lifecycle emitter secret to the new active value.
5. Send or observe a signed lifecycle event from ServiceNow and confirm the API records the event without authentication failures.
6. Remove `JEDI_LIFECYCLE_WEBHOOK_PREVIOUS_SECRET` after the emitter cutover and replay window have expired, then redeploy or restart the API service again.
7. Record the rotation date, operator, old-secret retirement time, verification event id, and deployment version in the customer operations log.

Other runtime secrets still require a coordinated secret-manager rotation and service restart unless a dedicated overlap setting exists. Rotate `JEDI_ADMIN_API_TOKEN`, ServiceNow OAuth client secrets, provider API keys, and alert webhook credentials using customer-approved maintenance windows, update dependent clients, and verify no rejected authentication events are logged after cutover.

Production startup validation rejects malformed model provider configuration. When `JEDI_MODEL_PROVIDER=openai`, `OPENAI_API_KEY` and `OPENAI_MODEL` are required and must not contain whitespace or control characters. Deployment should fail before the worker attempts outbound model calls if an environment manager injects a newline, tab, or padded provider value.

Production startup validation rejects malformed ServiceNow instance URLs. Configured `SERVICENOW_INSTANCE_URL`, `SERVICENOW_PM_INSTANCE_URL`, and `SERVICENOW_DEV_INSTANCE_URL` values must use HTTPS and must not include embedded credentials, URL fragments, raw or encoded whitespace, or control characters. Deployment should fail before webhook processing or worker fulfillment can connect to a non-TLS or ambiguous ServiceNow target.

Runtime settings loading also rejects malformed resolved ServiceNow instance URLs before settings are returned. Split `SERVICENOW_PM_INSTANCE_URL` and `SERVICENOW_DEV_INSTANCE_URL` values, including values resolved from legacy `SERVICENOW_INSTANCE_URL` fallback, must be HTTPS targets without credentials, fragments, whitespace, or control characters. Diagnostics name only the resolved setting and do not echo URL credentials, fragments, or encoded control values.

Direct `RuntimeSettings.servicenow_instance_url`, `RuntimeSettings.servicenow_pm_instance_url`, and `RuntimeSettings.servicenow_dev_instance_url` validation is exact-string guarded before production ServiceNow URL hygiene checks. `validate_runtime_settings()` rejects ServiceNow instance URL string subclasses or non-string objects with `<SETTING> must be a string runtime setting` before URL parsing, whitespace/control-character scans, encoded-control scans, HTTPS checks, credential checks, fragment checks, hostname checks, or production error aggregation. This prevents malformed direct runtime objects from reaching lower-level URL parsers while startup validates source and target ServiceNow instance boundaries.

Production startup validation also rejects malformed ServiceNow OAuth credentials. Configured `SERVICENOW_CLIENT_ID`, `SERVICENOW_CLIENT_SECRET`, `SERVICENOW_PM_CLIENT_ID`, `SERVICENOW_PM_CLIENT_SECRET`, `SERVICENOW_DEV_CLIENT_ID`, and `SERVICENOW_DEV_CLIENT_SECRET` values must not contain whitespace or control characters. Deployment should fail before token acquisition if an environment manager injects a newline, tab, or padded OAuth credential value.

Direct `RuntimeSettings.servicenow_client_id`, `RuntimeSettings.servicenow_client_secret`, `RuntimeSettings.servicenow_pm_client_id`, `RuntimeSettings.servicenow_pm_client_secret`, `RuntimeSettings.servicenow_dev_client_id`, and `RuntimeSettings.servicenow_dev_client_secret` validation is exact-string guarded before ServiceNow OAuth credential hygiene checks. `validate_runtime_settings()` rejects ServiceNow OAuth credential string subclasses or non-string objects with `<SETTING> must be a string runtime setting` before truthiness checks, padding checks, whitespace/control-character scans, or production error aggregation. This prevents malformed direct runtime credential objects from executing custom string, length, or strip behavior while startup validates source and target ServiceNow OAuth boundaries.

Runtime ServiceNow client construction uses the same exact-string and hygiene boundary before resolving PM/story and development-instance fallbacks. `_servicenow_story_client_from_settings()`, `_servicenow_development_client_from_settings()`, and `_servicenow_pm_and_dev_settings_match()` normalize `SERVICENOW_*`, `SERVICENOW_PM_*`, and `SERVICENOW_DEV_*` URL, client-id, and client-secret values before truthiness fallback, equality checks, OAuth credential construction, or `ServiceNowClient` construction. Malformed direct `RuntimeSettings` values fail as `RuntimeConfigError` diagnostics that name the setting instead of executing custom string, length, or equality hooks during split-client routing.

ServiceNow OAuth token responses are also treated as untrusted input. The client rejects missing, empty, non-ASCII, oversized, padded, whitespace-bearing, or control-character-bearing `access_token` values before caching the token or building a `Bearer` Authorization header. Token response values are capped at 8192 ASCII bytes before they can become an outbound credential. The diagnostic does not echo token values, token fragments, object representations, or credential-like payloads, and the client does not trim token response material into a usable credential.

ServiceNow OAuth access-token validation is type-safe before string handling. Access-token values must be exact `str` instances. Non-string values and string subclasses fail with `ServiceNow OAuth response did not include access_token` before ASCII checks, byte-length calculation, trim checks, whitespace/control-character scans, caching the token, building a `Bearer` Authorization header, or returning credentials to callers; the diagnostic does not echo object type names, object string output, token values, token fragments, or credential-like payloads.

ServiceNow OAuth, Table API, and Attachment API calls do not follow HTTP redirects. The urllib transport builds an explicit no-redirect opener and blocks any 3xx redirect before a second outbound request can be made. This keeps configured ServiceNow instance boundaries authoritative and prevents an instance, proxy, DNS, or network-control mistake from silently forwarding OAuth credentials, bearer tokens, story content, or delivery artifacts to another host.

ServiceNow HTTP error diagnostics are bounded at the transport boundary. Plain-text error bodies and string values inside JSON error bodies are truncated before they enter runtime diagnostics, while structured keys and short messages remain intact. The ServiceNow HTTP diagnostic cap includes the `...[truncated]` marker, so the truncation marker cannot push transport or API diagnostics beyond the configured maximum. ServiceNow API exception diagnostics also apply a final post-redaction size cap before formatting the error message, so alternate transports or future client paths cannot bypass bounded work-note, artifact, or operator-log diagnostics. ServiceNow API exception diagnostic text values must be exact `str` instances before redaction, whitespace normalization, or `repr()` formatting; string subclasses and unsupported scalar values render as `[non-json value]` instead of object type names, object string output, upstream body fragments, or credential-like payloads. Exact string diagnostic values are capped after redaction and whitespace normalization before they enter the structured diagnostic object. Diagnostic object keys are also projected before exception formatting: exact string keys are redacted, normalized, and bounded, duplicate rendered keys receive deterministic suffixes inside the same diagnostic key cap, and non-string keys render as `[non-json key]` without calling `str()` or `repr()` on the original key. This keeps upstream proxy or platform errors useful without allowing a remote response to create unbounded or reflective operator diagnostics.

ServiceNow API exception diagnostic traversal is cycle-safe. If an alternate transport or corrupted in-process response body supplies a cyclic exact dictionary, exact list, or exact tuple, the repeated active container renders as `[circular reference]` instead of raising a secondary recursion failure while formatting `ServiceNowApiError`. ServiceNow API diagnostics traverse only exact containers; dictionary, list, and tuple subclasses render as `[non-json value]` before `items()`, `len()`, iteration, or subclass hooks can execute.

Successful ServiceNow HTTP response parsing is also bounded at the transport boundary. Successful
responses must be valid UTF-8 strict JSON objects: valid UTF-8 JSON objects parsed with strict JSON
numeric handling. Invalid UTF-8, malformed JSON, non-standard JSON numeric constants such as `NaN`,
`Infinity`, and `-Infinity`, and non-object JSON response bodies fail as `ServiceNowApiError`
diagnostics without echoing upstream body fragments, credential-like keys, or response values.

Outbound ServiceNow JSON request bodies are strict JSON at the transport boundary. When an
`application/json` request body contains non-finite numeric values, the urllib transport rejects it
locally with `ServiceNow JSON request body contains non-finite numeric values` before opening a
network request. The diagnostic does not echo request field names, body values, or credential-like
payload fragments.
ServiceNow transport JSON request bodies are validated before serialization. JSON request bodies must
contain only exact JSON containers and scalars: dictionaries with exact string keys, exact lists,
null, exact strings, exact booleans, exact integers, and finite exact floats. String subclasses,
integer subclasses, float subclasses, tuple containers, bytes, and arbitrary Python objects fail with
`ServiceNow JSON request body contains non-JSON values` before `json.dumps()`, implicit conversion,
opener construction, or credential-bearing scalar hooks can execute.
ServiceNow transport JSON request bodies are cycle-safe and depth-bounded before serialization.
Active dictionary and list containers are tracked during recursive validation so cyclic payloads fail
with `ServiceNow JSON request body contains circular references` before raw `RecursionError`,
`json.dumps()`, or opener construction. Request JSON nesting deeper than 100 containers fails with
`ServiceNow JSON request body is too deeply nested` before serialization or network construction.

ServiceNow transport JSON encoding diagnostics do not retain unsafe causes. Non-finite numeric JSON
request bodies fail with `ServiceNow JSON request body contains non-finite numeric values`, and
unsupported JSON keys or values fail with `ServiceNow JSON request body contains non-JSON values`.
Those public `ServiceNowApiError` instances suppress the original validator or serializer exception,
so crash reporters, traceback formatters, and work-note writers do not retain payload-derived field
names, object type names, object representations, or credential-bearing exception text in
`__cause__`.

ServiceNow table/list response handling also validates successful `result` shapes before record parsing. List-style client methods require `result` to be present and to be a list of objects; missing or malformed list shapes fail with fixed `ServiceNowApiError` diagnostics without echoing the malformed `result` value or upstream response fragments. ServiceNow table/list response handling requires successful responses to include `result` so malformed upstream responses cannot silently become empty record lists.

ServiceNow single-record response handling validates successful `result` shapes before returning create, update, upsert, or attachment metadata to callers. Single-object client methods require `result` to be present and to be an object; missing or malformed object shapes fail with fixed `ServiceNowApiError` diagnostics without echoing the malformed `result` value or upstream response fragments. ServiceNow single-record response handling requires successful responses to include `result` so malformed upstream responses cannot silently become empty metadata objects.

ServiceNow upsert lookup handling is strict as well. When `ServiceNowClient.upsert_table_record()` finds an existing Table API record, it accepts only primitive string, boolean, and integer scalar values for the existing record `sys_id` before building the PATCH URL. Upsert lookup response text values must be exact `str` instances; string subclasses fail with `ServiceNow API lookup contains non-JSON value` before record-id validation or PATCH URL construction. Unsupported ServiceNow response values fail with `ServiceNow API lookup contains non-JSON value`; the client does not call `str()` or `repr()` on unsupported lookup response values.

ServiceNow Table API lookup query construction is delimiter-safe and bounded. `ServiceNowClient.fetch_table_record()` and `ServiceNowClient.fetch_table_records()` reject lookup keys or values containing `^`, `=`, control characters, or more than 1024 characters before OAuth token acquisition, GET construction, encoded-query assembly, or Table API transport. Unsafe or oversized lookup parts fail with `ServiceNow API lookup query is unsafe`; the diagnostic does not echo lookup values, credential-like fragments, or query text.
`ServiceNowClient.fetch_table_record()` and `ServiceNowClient.upsert_table_record()` reject empty lookup bodies. An empty lookup would otherwise produce an empty encoded query and could read or patch the first arbitrary table record returned by ServiceNow, so empty lookup dictionaries fail with `ServiceNow API lookup body must not be empty` before OAuth token acquisition, GET construction, upsert lookup decisions, mutation construction, or Table API transport.

ServiceNow lookup query construction is type-safe before delimiter checks and bounded before request construction. The shared lookup-part guard rejects non-string lookup keys and values, requires lookup keys and values must be exact `str` instances before encoded-query assembly, delimiter checks, length checks, control-character scans, OAuth acquisition, or request construction, and rejects lookup parts longer than 1024 characters before OAuth acquisition or request construction. Non-string values, string subclasses, oversized values, and malformed values fail with `ServiceNow API lookup query is unsafe`, so hostile, broken, subclassed, or oversized lookup objects cannot leak object type names, object string output, lookup values, query fragments, or credential-like payloads into diagnostics.

`ServiceNowClient.fetch_stories()` validates raw story `sysparm_query` values before request construction. Explicit story queries must be exact, non-empty, unpadded strings within the lookup-part ceiling and without ASCII control characters; unsafe queries fail with `ServiceNow API story query is unsafe` before truthiness checks, OAuth token acquisition, GET construction, or Table API transport. The guard allows normal ServiceNow encoded-query delimiters such as `^` and `=`, but it does not echo query values, object type names, object string output, or credential-like fragments in diagnostics.

ServiceNow Table API field projection construction is delimiter-safe and bounded. `ServiceNowClient.fetch_table_records(fields=...)` accepts only unpadded ServiceNow field identifiers, including dotted reference paths made of identifier parts, no longer than 256 characters before joining them into `sysparm_fields`. Unsafe or oversized field names fail with `ServiceNow API field name is unsafe` before OAuth token acquisition, GET construction, or Table API transport; the diagnostic does not echo field values, field names, projection fragments, or credential-like payloads.
`ServiceNowClient.fetch_table_records(fields=...)` validates provided field lists before truthiness branching. `None` still omits `sysparm_fields`; any provided field list must be an exact list before the method decides whether to include the projection parameter, so hostile list truthiness, iteration, stringification, or representation hooks cannot run or leak credentials before fixed field-list diagnostics.
`ServiceNowClient.fetch_table_records(fields=...)` rejects empty provided field lists. `None` remains the only supported way to omit `sysparm_fields`; an explicit empty list fails with `ServiceNow API field list must not be empty` before OAuth token acquisition, GET construction, or Table API transport.

ServiceNow field-name validation is type-safe before string handling and bounded before request construction. The shared field-name guard rejects non-string values before calling string methods or regex matching, and rejects values longer than 256 characters before OAuth acquisition or request construction. Field-name values must be exact `str` instances. Hostile, broken, subclassed, or oversized field-key objects cannot leak object type names, object string output, field names, body fragments, projection fragments, or credential-like payloads into diagnostics. Non-string, string subclasses, oversized, and malformed field names fail with `ServiceNow API field name is unsafe`.

ServiceNow story PATCH body field names are delimiter-safe and bounded. `ServiceNowClient.update_story_fields()` validates every PATCH body field name with the shared ServiceNow field identifier rule before constructing the `rm_story` PATCH request. Unsafe or oversized field names fail with `ServiceNow API field name is unsafe` before OAuth token acquisition, PATCH construction, or Table API transport; the diagnostic does not echo field names, body fragments, or credential-like payloads.

Generic ServiceNow Table API upsert body field names are delimiter-safe and bounded. `ServiceNowClient.upsert_table_record()` validates every create/update body field name with the shared ServiceNow field identifier rule before OAuth token acquisition, lookup, POST construction, PATCH construction, or Table API transport. Unsafe or oversized field names fail with `ServiceNow API field name is unsafe`; the diagnostic does not echo field names, body fragments, lookup values, or credential-like payloads.

ServiceNow dictionary field creation validates element names before writing configuration. `ServiceNowClient.create_story_dictionary_field()` accepts only unpadded ServiceNow field identifiers for the `element` body field before constructing the `sys_dictionary` POST. Unsafe element names fail with `ServiceNow API field name is unsafe` before OAuth token acquisition, POST construction, or Table API transport; the diagnostic does not echo element values, encoded-query fragments, or credential-like payloads.

ServiceNow dictionary field creation validates column labels before writing configuration. `ServiceNowClient.create_story_dictionary_field()` allows normal human labels with spaces for the `column_label` body field while rejecting non-string values, blank labels, trim-padded labels, control characters, and labels over 255 characters before constructing the `sys_dictionary` POST. Unsafe column labels fail with `ServiceNow dictionary column label is unsafe` before OAuth token acquisition, POST construction, or Table API transport; the diagnostic does not echo column-label values, body fragments, or credential-like payloads.

ServiceNow dictionary column-label validation is type-safe before string handling. Column-label values must be exact `str` instances. Non-string values and string subclasses fail with `ServiceNow dictionary column label is unsafe` before blank-label checks, string methods, length checks, control-character scans, dictionary request body construction, OAuth token acquisition, or transport calls; the diagnostic does not echo object type names, object string output, column-label values, body fragments, or credential-like payloads.

ServiceNow dictionary field creation validates internal types before writing configuration. `ServiceNowClient.create_story_dictionary_field()` accepts only string, unpadded ServiceNow identifier-style type names no longer than 128 characters for the `internal_type` body field before constructing the `sys_dictionary` POST. Non-string and unsafe internal types fail with `ServiceNow dictionary internal type is unsafe` before OAuth token acquisition, POST construction, string-method calls, or Table API transport; oversized internal types use the same fixed diagnostic. The diagnostic does not echo internal type values, body fragments, credential-like payloads, object type names, or object string output.

ServiceNow dictionary internal-type validation is type-safe before string handling. Internal-type values must be exact `str` instances. Non-string values and string subclasses fail with `ServiceNow dictionary internal type is unsafe` before string methods, length checks, regex matching, dictionary request body construction, OAuth token acquisition, or transport calls; the diagnostic does not echo object type names, object string output, internal type values, body fragments, or credential-like payloads.

ServiceNow dictionary field creation validates max lengths before writing configuration. `ServiceNowClient.create_story_dictionary_field()` accepts only real Python integers from 1 through 65535 for the optional `max_length` body field before constructing the `sys_dictionary` POST. Unsafe max lengths fail with `ServiceNow dictionary max length is unsafe` before OAuth token acquisition, POST construction, or Table API transport; the diagnostic does not echo max-length values, body fragments, or credential-like payloads.

ServiceNow Table API result limits are bounded before request construction. `ServiceNowClient.fetch_stories()` and `ServiceNowClient.fetch_table_records()` accept only integer `limit` values from 1 through 500 before converting them to `sysparm_limit`. Non-integer, non-positive, boolean, or oversized limits fail with `ServiceNow API result limit is unsafe` before OAuth token acquisition, GET construction, numeric comparison, or Table API transport; the diagnostic does not echo query values, lookup values, or credential-like payloads, and does not echo object type names or object string output.

ServiceNow boolean query/body flags are strict before serialization. Shared ServiceNow flag serialization accepts only actual Python `bool` values before producing `true` or `false` strings for dictionary `read_only`, CI/CD retrieve flags, and CI/CD commit `force_commit`. Non-bool values fail with `ServiceNow API boolean value is unsafe` before OAuth token acquisition, request construction, or API transport; the diagnostic does not echo flag values, object representations, or credential-like payloads.

Ready-story project filters are delimiter-safe before encoded-query construction. `ServiceNowClient.fetch_ready_stories(project_sys_id=...)` validates `project_sys_id` with the same ServiceNow record-id rule used for URL path ids before appending it to `state=Ready^project=<id>`. Unsafe project ids fail with `ServiceNow API record id is unsafe` before OAuth token acquisition, GET construction, or Table API transport; the diagnostic does not echo project id values, encoded-query fragments, or credential-like payloads.
`ServiceNowClient.fetch_ready_stories(project_sys_id=...)` validates provided project ids before truthiness branching. `None` still means no project filter, but any provided project id must be an exact record-id string before the method decides whether to append a project clause, so hostile scalar truthiness, stringification, or representation hooks cannot run or leak credentials before the fixed `ServiceNow API record id is unsafe` diagnostic.

Generic ServiceNow Table API table names are path-safe. `ServiceNowClient.upsert_table_record()`, `ServiceNowClient.fetch_table_record()`, and `ServiceNowClient.fetch_table_records()` accept only unpadded table names made of letters, digits, and underscores, starting with a letter, and no longer than 128 characters before constructing `/api/now/table/{table}` URLs. Unsafe or oversized table names fail with `ServiceNow API table name is unsafe` before OAuth token acquisition or request construction; the diagnostic does not echo table values, URL fragments, or credential-like payloads.

ServiceNow table-name validation is type-safe before string handling and bounded before request construction. The shared table-name guard rejects non-string values before calling string methods or regex matching, and rejects values longer than 128 characters before OAuth acquisition or request construction. Table-name values must be exact `str` instances. Hostile, broken, subclassed, or oversized table-name inputs cannot leak object type names, object string output, table values, URL fragments, or credential-like payloads into diagnostics. Non-string, string subclasses, oversized, and malformed table names fail with `ServiceNow API table name is unsafe`.

ServiceNow Table API record ids used in URL paths are path-safe as well. `ServiceNowClient.update_story_fields()` and the PATCH branch of `ServiceNowClient.upsert_table_record()` accept only unpadded record id path segments made of letters, digits, underscores, and hyphens and no longer than 128 characters before constructing `/api/now/table/{table}/{sys_id}` URLs. Unsafe or oversized record ids fail with `ServiceNow API record id is unsafe` before OAuth token acquisition or request construction; the diagnostic does not echo record id values, URL fragments, or credential-like payloads.

ServiceNow record-id validation is type-safe before string handling and bounded before request construction. The shared record-id guard rejects non-string values before calling string methods or regex matching, and rejects values longer than 128 characters before OAuth acquisition or request construction. Record-id values must be exact `str` instances. Hostile, broken, subclassed, or oversized record-id inputs cannot leak object type names, object string output, record id values, URL fragments, query fragments, or credential-like payloads into diagnostics. Non-string, string subclasses, oversized, and malformed record ids fail with `ServiceNow API record id is unsafe`.

ServiceNow story response text is type-safe before model construction. `ServiceNowClient.fetch_stories()` accepts only string values for required story text fields, optional acceptance criteria, and AI additional-context fields returned by ServiceNow or an alternate transport. Story response text values must be exact `str` instances. Non-string values and string subclasses fail with `ServiceNow API story response field is unsafe` before optional acceptance-criteria trimming, additional-context length checks, `Story` model construction, automation routing, operational views, artifact persistence, or failure-writeback decisions; the diagnostic does not echo object type names, object string output, story values, additional-context values, or credential-like payloads. AI additional-context values are operational references and status fields, so they are also bounded to 1024 characters before `Story.additional_context` is constructed; oversized additional-context values use the same fixed diagnostic without echoing submitted context values.

ServiceNow story response story-point values are strict before model construction. `ServiceNowClient.fetch_stories()` accepts only actual non-boolean finite non-negative integers or floats and simple ASCII decimal strings for story `story_points` values returned by ServiceNow or an alternate transport. Story-point numeric values must be exact `int` or exact `float` instances. Missing, null, or blank story-point values still map to the operational default `0.0`; non-string objects, numeric subclasses, booleans, negative values, signed strings, whitespace-padded values, non-ASCII digits, exponent notation, non-finite values, and malformed strings fail with `ServiceNow API story response field is unsafe` before a `Story` is constructed; the diagnostic does not echo object type names, object string output, story-point values, story values, or credential-like payloads.

ServiceNow story response priority values are strict before model construction. `ServiceNowClient.fetch_stories()` accepts only actual non-boolean integers and simple ASCII decimal strings for story `priority` values returned by ServiceNow or an alternate transport. Priority numeric values must be exact `int` instances. Missing, null, or blank priority values still map to the operational default `5`; non-string objects, integer subclasses, booleans, signed values, whitespace-padded values, non-ASCII digits, and malformed strings fail with `ServiceNow API story response field is unsafe` before a `Story` is constructed; the diagnostic does not echo object type names, object string output, priority values, story values, or credential-like payloads.

ServiceNow metadata response text is type-safe before model construction and bounded before metadata model construction. `ServiceNowClient.fetch_story_state_choices()` and `ServiceNowClient.fetch_story_dictionary_fields()` accept only string values for state-choice labels/values and dictionary `element`, `column_label`, and `internal_type` fields returned by ServiceNow or an alternate transport; those values must be exact `str` instances, no longer than 1024 characters, and must not contain ASCII control characters. Non-string or oversized metadata response text fails with `ServiceNow API metadata response field is unsafe` before `StoryStateChoice` or `StoryDictionaryField` models are constructed; control-character metadata response text fails with the same diagnostic, and string subclasses fail with the same diagnostic. The diagnostic does not echo object type names, object string output, metadata values, dictionary values, state-choice values, or credential-like payloads.

ServiceNow metadata response booleans are strict before model construction. `ServiceNowClient.fetch_story_state_choices()` and `ServiceNowClient.fetch_story_dictionary_fields()` accept only actual booleans and explicit string boolean values for state-choice `inactive` flags and dictionary `active` or `read_only` flags returned by ServiceNow or an alternate transport; string boolean values must be unpadded and must be exact `str` instances. Non-string objects and malformed boolean strings fail with `ServiceNow API metadata response field is unsafe` before `StoryStateChoice` or `StoryDictionaryField` models are constructed; string subclasses and padded boolean strings fail with the same diagnostic. The diagnostic does not echo object type names, object string output, metadata flag values, dictionary values, state-choice values, or credential-like payloads.

Bootstrap story metadata planning validates dictionary-field collection shape before initialization decisions. `plan_bootstrap_fields()` accepts only exact Python lists containing exact `StoryDictionaryField` records. List subclasses, alternate iterables, model subclasses, and malformed entries fail with `bootstrap dictionary fields contain non-JSON value` before iteration hooks, model hooks, active-field filtering, missing-field decisions, writable-field decisions, or bootstrap apply planning can consume caller-controlled behavior.

Bootstrap apply validates ServiceNow mutation response shape before recording applied work. `apply_bootstrap_fields()` accepts only exact Python dictionaries from `create_story_dictionary_field()` and `upsert_table_record()`, including dictionary writable-field remediation and the platform read-only UI policy upsert. Create-field response subclasses fail with `bootstrap create field result is unsafe`; table upsert response subclasses fail with `bootstrap table upsert result is unsafe`. Both diagnostics are fixed and do not echo object type names, object string output, response values, or credential-like payloads, and failures happen before truthiness hooks, length hooks, created-field recording, writable-field recording, platform-read-only result recording, or bootstrap apply result construction can consume caller-controlled response behavior.

ServiceNow metadata response sequence values are strict before state-choice sorting. `ServiceNowClient.fetch_story_state_choices()` accepts only actual non-boolean integers and simple ASCII decimal strings for `sys_choice.sequence` values returned by ServiceNow or an alternate transport, and accepted sequence values must fit `0..2147483647`. Numeric sequence values must be exact `int` instances. Sequence string values must be exact `str` instances. Missing or blank sequence values map to `0`; non-string objects, integer subclasses, string subclasses, booleans, signed values, whitespace-padded values, non-ASCII digits, out-of-range values, oversized decimal strings, and malformed strings fail with `ServiceNow API metadata response field is unsafe` before `StoryStateChoice` models are constructed; the diagnostic does not echo object type names, object string output, sequence values, state-choice values, or credential-like payloads.

ServiceNow CI/CD Update Set path ids use the same record-id safety rule. `ServiceNowClient.preview_cicd_update_set()`, `ServiceNowClient.commit_cicd_update_set()`, and `ServiceNowClient.fetch_cicd_progress()` validate `remote_update_set_id` and `progress_id` values before constructing `/api/sn_cicd/update_set/{action}/{id}` or `/api/sn_cicd/progress/{id}` URLs. `ServiceNowClient.retrieve_cicd_update_set()` validates `update_set_id`, `update_source_id`, and `update_source_instance_id` before adding them to retrieve query parameters. Unsafe CI/CD ids fail with `ServiceNow API record id is unsafe` before OAuth token acquisition or request construction; the diagnostic does not echo CI/CD ids, URL fragments, query fragments, or credential-like payloads.
`ServiceNowClient.retrieve_cicd_update_set()` validates optional source ids before truthiness branching. `None` still omits the optional `update_source_id` and `update_source_instance_id` parameters, but any provided source id must pass the shared record-id guard before the method decides whether to include the parameter, so hostile scalar truthiness, stringification, or representation hooks cannot run before fixed CI/CD id diagnostics.
`ServiceNowClient.probe_cicd_update_set_endpoint()` validates probe actions before membership checks. Probe actions must be exact strings from the supported allowlist, currently `create` and `retrieve`; unsafe actions fail with `ServiceNow CI/CD probe action is unsafe` before membership checks, OAuth token acquisition, URL construction, request construction, or API transport. The diagnostic does not echo action values, object type names, object string output, URL fragments, or credential-like payloads.
`ServiceNowClient._send_cicd_update_set_request()` validates optional params and body containers before truthiness branching. `None` still omits optional query parameters and JSON body values, but any provided container must be an exact dictionary before the helper decides whether to substitute an empty dictionary, so hostile container truthiness, stringification, or representation hooks cannot run before fixed CI/CD request-container diagnostics.
`ServiceNowClient._send_cicd_update_set_request()` validates CI/CD request methods and actions before URL construction. Methods must pass the shared ServiceNow request-method guard, and CI/CD actions must be exact strings matching supported helper paths such as `retrieve`, `preview/{sys_id}`, or `commit/{sys_id}` before the helper interpolates `/api/sn_cicd/update_set/{action}`. Unsafe methods and actions fail before OAuth token acquisition, URL construction, request construction, or transport; diagnostics do not echo method values, action values, object type names, object string output, URL fragments, query fragments, or credential-like payloads.

Discovered ServiceNow Scripted REST operation URIs are path-safe before use and bounded before request construction. `ServiceNowClient.import_update_set_xml()` accepts only operation URIs shaped like `/api/<namespace>/<service>` and no longer than 256 characters from `sys_ws_operation.operation_uri` before appending them to the configured instance URL. Unsafe or oversized operation URIs fail with `ServiceNow API operation URI is unsafe` before the import POST is constructed; the diagnostic does not echo operation URI values, URL fragments, query strings, or credential-like payloads.

Discovered ServiceNow Scripted REST operation URI validation is type-safe before string handling. Operation URI values must be exact `str` instances. Non-string values and string subclasses fail with `ServiceNow API operation URI is unsafe` before string methods, length checks, regex matching, import POST URL construction, or transport calls; the diagnostic does not echo object type names, object string output, operation URI values, URL fragments, query strings, or credential-like payloads.

Parsed ServiceNow HTTP error JSON diagnostics are traversal-bounded before the payload leaves the transport. Large exact dictionaries, exact lists, and exact tuples are sampled with bounded iterators and receive `omitted_fields` or `omitted_items` markers before recursive string truncation continues. Dictionary, list, and tuple subclasses render as `[non-json value]` before `items()`, `len()`, iteration, or subclass hooks can execute. Parsed HTTP error diagnostic text values must be exact `str` instances before normalization and truncation; string subclasses render as `[non-json value]` instead of object type names, object string output, upstream body fragments, or credential-like payloads. Parsed HTTP error diagnostic exact string values collapse whitespace/control-character runs before the shared cap is applied, so lower-level transport diagnostics cannot retain raw multiline text. Parsed HTTP error diagnostic object keys are projected before response propagation: exact string keys are whitespace/control-character-normalized and bounded, duplicate rendered keys receive deterministic suffixes, and non-string keys render as `[non-json key]` without calling `str()` or `repr()` on the original key. Parsed HTTP error diagnostic scalar values are JSON-safe before response propagation: `None`, booleans, integers, finite floats, and exact strings remain useful, while non-finite floats and unsupported Python objects render as `[non-json value]`. Parsed HTTP error diagnostic traversal is also cycle-safe; repeated active containers render as `[circular reference]` before response propagation instead of raising secondary recursion failures. Internal dictionary truncation markers are inserted through the same collision-safe key renderer, so a user-provided `__jedi_response_truncated__` key remains visible and the internal marker receives a deterministic suffix. This prevents a wide, cyclic, or Python-specific upstream JSON error response from forcing diagnostic shaping across every nested entry or reflecting unsafe diagnostic values.

ServiceNow HTTP error response JSON parsing is strict as well. Structured error bodies containing
non-standard JSON numeric constants such as `NaN`, `Infinity`, or `-Infinity` are reduced to the
fixed `ServiceNow API error response body is not valid JSON` diagnostic instead of preserving
non-finite values, submitted field names, credential-like keys, or upstream response fragments.

ServiceNow API response diagnostics are traversal-bounded before final formatting. Large exact dictionary, exact list, and exact tuple response values are sampled up to the ServiceNow diagnostic collection-item cap and include `omitted_fields` or `omitted_items` markers before `repr()` and the final diagnostic cap. Dictionary, list, and tuple subclasses render as `[non-json value]` before subclass traversal methods can execute. Internal dictionary truncation markers use collision-safe key rendering, preserving a user-provided `__jedi_response_truncated__` diagnostic key and moving the internal marker to a deterministic duplicate key when needed. This prevents a wide ServiceNow or API mock response from forcing recursive redaction of every nested entry before the bounded exception string is produced.

ServiceNow HTTP error response reads are also bounded before diagnostic shaping. The urllib transport reads at most 10 MiB plus one sentinel byte from HTTP error responses and returns a compact oversized-body diagnostic when the cap is exceeded, so a large upstream error cannot create unbounded memory pressure before truncation runs.

Successful ServiceNow response bodies are also bounded at the transport boundary. The urllib transport reads at most 10 MiB plus one sentinel byte before JSON parsing and rejects oversized successful responses before they can create unbounded memory pressure.

Direct ServiceNow boundary model validation suppresses rejected input values in Pydantic validation errors. `ServiceNowSettings`, `HttpRequest`, `HttpResponse`, story state choices, and story dictionary field models still name invalid fields, but type or parsing failures do not echo rejected instance URLs, request URLs, header values, request body fragments, response status text, or live instance metadata into logs, artifacts, or ServiceNow work notes.

Production also rejects non-positive request body, rate-limit, timeout, and public-web size
settings. Runtime settings loading rejects malformed public documentation retrieval settings
whenever public documentation retrieval is enabled with `JEDI_PUBLIC_WEB_ACCESS=worker`. In that mode,
every `JEDI_PUBLIC_WEB_DOC_URLS` entry must be an HTTPS URL whose host exactly matches
`JEDI_PUBLIC_WEB_ALLOWED_DOMAINS`; allowed domains must be non-local hostnames without padding,
whitespace, or control characters. Mismatched, non-HTTPS, credentialed, fragmented,
whitespace/control-character, encoded-whitespace/control-character, or sensitive-query
documentation URLs fail before runtime settings are returned, and production startup validation
keeps the same direct-settings boundary. Worker public documentation retrieval also rejects embedded URL
credentials, fragments, raw or encoded whitespace/control characters, and sensitive query
parameters before transport, and blocks private, loopback, link-local, reserved, multicast, and
legacy numeric local targets such as `2130706433` or `2852039166` even if a domain allowlist is
misconfigured. Production startup rejects public documentation URLs whose normalized host is
localhost, delegated `.localhost`, private, loopback, link-local, reserved, multicast,
unspecified, or legacy numeric local; credentialed documentation URLs are never valid public
documentation sources.

Runtime settings loading also validates configured public-web allowlist and documentation URL
values when `JEDI_PUBLIC_WEB_ACCESS` is left disabled. Disabled mode does not require `JEDI_PUBLIC_WEB_ALLOWED_DOMAINS` or `JEDI_PUBLIC_WEB_DOC_URLS`, but if either setting is present it must satisfy the same non-local allowlist, HTTPS URL, credential-free, fragment-free, whitespace/control-character-free, encoded-control-free, sensitive-query-free, and allowlist-match rules used by worker mode. This prevents dormant public-web configuration from carrying an unsafe endpoint that later becomes active through a single feature-flag change.

Production validation for direct `RuntimeSettings` public-web values does not echo raw invalid
allowlist entries or documentation URLs. If a direct settings object contains URL userinfo,
sensitive query parameters, fragments, encoded control characters, or private/local hostnames,
startup diagnostics name `JEDI_PUBLIC_WEB_ALLOWED_DOMAINS` or `JEDI_PUBLIC_WEB_DOC_URLS` and
describe the violated rule without returning the configured URL or host fragment.
Direct public-web allowlist and documentation URL collections are exact-list guarded before outbound retrieval validation. `validate_runtime_settings()` rejects non-list containers, string subclasses, and non-string entries with `JEDI_PUBLIC_WEB_ALLOWED_DOMAINS must be a string list setting` or `JEDI_PUBLIC_WEB_DOC_URLS must be a string list setting` before truthiness checks, hostname normalization, `.strip()`, URL parsing, allowlist matching, or production error aggregation. This prevents malformed direct runtime objects from executing collection or string hooks while startup validates public-documentation egress controls.

Production startup also caps public documentation retrieval resource limits:
`JEDI_PUBLIC_WEB_TIMEOUT_SECONDS<=30`, `JEDI_PUBLIC_WEB_MAX_RESPONSE_BYTES<=1048576`,
`JEDI_PUBLIC_WEB_MAX_EXCERPT_CHARS<=16000`, and `JEDI_PUBLIC_WEB_MAX_RESULTS<=10`. Oversized direct
settings fail startup with setting-name and ceiling diagnostics instead of echoing the configured
value, and worker loops cannot be stalled by multi-minute outbound waits.
Direct integer runtime settings are exact-integer guarded before production range checks. `validate_runtime_settings()` rejects int subclasses, booleans, floats, strings, or non-integer objects with `<SETTING> must be an integer runtime setting` before comparison operators, positive-value checks, maximum caps, or production error aggregation. This applies to lifecycle webhook body and skew limits, lifecycle and admin rate limits, admin body limits, HSTS max-age, stale-job requeue windows, alert webhook body limits, and public-web size and result limits, preventing malformed direct runtime objects from executing numeric comparison hooks during startup validation.
Direct outbound timeout runtime settings are exact finite-number guarded before production range checks. `validate_runtime_settings()` rejects float subclasses, booleans, strings, non-finite floats, or non-number objects with `<SETTING> must be a finite number runtime setting` before comparison operators, positive-value checks, maximum caps, or production error aggregation. This applies to `JEDI_ALERT_WEBHOOK_TIMEOUT_SECONDS` and `JEDI_PUBLIC_WEB_TIMEOUT_SECONDS`, preventing malformed direct runtime objects from executing numeric comparison hooks while startup validates outbound wait ceilings.
Direct boolean runtime settings are exact-boolean guarded before production policy checks. `validate_runtime_settings()` rejects truthy or falsey objects, integers, strings, or non-boolean values with `<SETTING> must be a boolean runtime setting` before `__bool__` execution, role-policy checks, fail-closed classifier validation, HSTS enforcement, build-claim application, legacy Update Set apply checks, alert webhook checks, or production error aggregation. This applies to `JEDI_ALLOW_COMBINED_PRODUCTION`, `JEDI_BUILD_CLAIM_APPLY`, `JEDI_STRICT_TRANSPORT_SECURITY_ENABLED`, `JEDI_ALERT_WEBHOOK_ENABLED`, `JEDI_UPDATE_SET_APPLY`, and `JEDI_CLASSIFIER_GATE`.

Comma-separated public-web allowlist and documentation URL entries preserve interior padding for
validation, so values such as `docs.servicenow.com, developer.servicenow.com` or
`https://docs.servicenow.com/a, https://developer.servicenow.com/b` fail settings loading when
worker public documentation retrieval is enabled, and fail production validation for direct
settings wiring, instead of being silently normalized. Empty CSV entries are also rejected, so
values with doubled commas or trailing commas such as `docs.servicenow.com,,developer.servicenow.com`
or `https://docs.servicenow.com/a,` fail settings loading with the setting name instead of being
silently dropped.
Runtime CSV parsing is exact-string guarded before splitting. `_csv_values()` rejects string
subclasses and non-string objects with `<SETTING> must be a string runtime setting` before `.split()`,
empty-item checks, public-web allowlist validation, documentation URL validation, or runtime settings
construction. This prevents malformed in-process configuration maps from executing CSV string hooks
or leaking object type names while parsing public-web runtime controls.
If the legacy `JEDI_UPDATE_SET_APPLY=true` path is explicitly enabled, `JEDI_UPDATE_SET_USER_NAME`
must be set so any legacy local apply action has an operator identity in audit context. Production startup validation rejects `JEDI_UPDATE_SET_USER_NAME` values containing whitespace or control characters because the value is audit metadata. Runtime settings loading rejects empty, padded, or control-character `JEDI_UPDATE_SET_USER_NAME` values before settings are returned, and production startup validation rejects malformed direct values because the value is audit metadata.
Direct `RuntimeSettings.update_set_user_name` validation is exact-string guarded before legacy local apply operator checks. `validate_runtime_settings()` rejects update-set user name string subclasses or non-string objects with `JEDI_UPDATE_SET_USER_NAME must be a string runtime setting` before truthiness checks, control-character scans, or production error aggregation. This prevents malformed direct runtime objects from executing operator-identity hooks while startup validates local Update Set apply audit metadata.

Legacy local Update Set apply lookup handling is strict. `apply_candidate_to_update_set()` accepts only primitive string, boolean, and integer scalar values for the integration user lookup `sys_user.sys_id` before setting the current Update Set preference or applying dictionary/form changes. Unsupported objects, bytes, containers in scalar positions, floats, and non-scalar values fail with `Update Set apply lookup contains non-JSON value` before any local ServiceNow mutation, customer-update fetch, or apply result reporting. The legacy apply lookup path does not call `str()` or `repr()` on unsupported ServiceNow response values.

Direct Update Set apply form layout planning requires matched `sys_ui_section` records to include `sys_id`. Missing section identifiers fail with `Update Set apply metadata field is missing` before `sys_ui_element` lookup, form-layout upsert, customer-update fetch, or apply result reporting, so legacy local apply cannot silently create form layout updates against a blank section reference.

Direct Update Set apply form metadata conversion accepts only primitive string, boolean, and integer scalar values. Unsupported objects, bytes, containers in scalar positions, floats, and non-scalar values fail with `Update Set apply metadata contains non-JSON value` before section filtering, `sys_ui_element` lookup, form-layout upsert, customer-update fetch, or apply result reporting. The metadata path does not call `str()` or `repr()` on unsupported ServiceNow response values.

Direct Update Set apply form element position parsing uses the same primitive-only metadata boundary. Unsupported `sys_ui_element.position` values fail with `Update Set apply metadata contains non-JSON value` before insertion-position calculation, shifted-element planning, form-layout upsert, customer-update fetch, or apply result reporting. Position parsing does not call `str()` or `repr()` on unsupported ServiceNow response values.

Direct Update Set apply form element position parsing also fails closed on malformed primitive position values. Non-integer `sys_ui_element.position` text fails with `Update Set apply position field is invalid` before insertion-position calculation, shifted-element planning, form-layout upsert, customer-update fetch, or apply result reporting. Invalid position diagnostics do not echo the rejected ServiceNow response value.

Direct Update Set apply section view filtering uses the primitive-only metadata boundary. Unsupported `sys_ui_section.view` reference values fail with `Update Set apply metadata contains non-JSON value` before default-view filtering, `sys_ui_element` lookup, form-layout upsert, customer-update fetch, or apply result reporting. View filtering does not call `str()` or `repr()` on unsupported ServiceNow response values.

Direct Update Set apply reference metadata dictionaries are exact containers. Section view filtering
and metadata reference extraction accept only exact dictionaries before `value` or `display_value`
lookup. Dictionary subclasses fail with `Update Set apply metadata contains non-JSON value` before
default-view filtering, section matching, form-layout upsert, customer-update fetch, or apply result
reporting can execute caller-controlled dictionary accessors.

Direct Update Set apply form element name comparisons use the primitive-only metadata boundary. Unsupported `sys_ui_element.element` values fail with `Update Set apply metadata contains non-JSON value` before description-anchor matching, shifted-element planning, form-layout upsert, customer-update fetch, or apply result reporting. Element comparisons do not call `str()` or `repr()` on unsupported ServiceNow response values.

Direct Update Set apply form layout candidate fields use a primitive-only input boundary. Unsupported model-provided form table, view, section, and target-field values fail with `Update Set apply candidate field contains non-JSON value` before section lookup, metadata filtering, form-layout upsert, customer-update fetch, or apply result reporting. Candidate form planning does not call `str()` or `repr()` on unsupported model values.

Direct Update Set apply dictionary candidate fields use a primitive-only input boundary. Unsupported model-provided dictionary table, element, label, type, length, default, reference, mandatory, and help values fail with `Update Set apply candidate field contains non-JSON value` before integration-user lookup, current Update Set preference changes, dictionary upsert, customer-update fetch, or apply result reporting. Dictionary candidate normalization does not call `str()` or `repr()` on unsupported model values.

Direct Update Set apply candidate text fields require exact strings. String subclasses fail with the same candidate non-JSON diagnostic before dictionary normalization, form-layout planning, integration-user lookup, current Update Set preference changes, dictionary upsert, form-layout upsert, customer-update fetch, or apply result reporting.

Direct Update Set apply ServiceNow response text values require exact strings. String subclasses from legacy local apply lookups or metadata fetches fail with the existing lookup or metadata non-JSON diagnostic before current Update Set preference changes, dictionary upsert, form-layout upsert, customer-update fetch, or apply result reporting.

Direct Update Set apply XML-backed form candidate parsing requires exact strings. Unsupported or subclassed `sys_ui_form.elements` values fail with `Update Set apply candidate field contains non-JSON value` before XML attribute parsing, section lookup, metadata filtering, form-layout upsert, customer-update fetch, or apply result reporting.

Direct Update Set apply form placement candidate fields use the candidate primitive boundary. Unsupported model-provided position, position hint, placement, location, or rationale values fail with `Update Set apply candidate field contains non-JSON value` before description-anchor matching, section lookup, metadata filtering, form-layout upsert, customer-update fetch, or apply result reporting.

Direct Update Set apply request identifiers require exact strings. Corrupted in-process `update_set_sys_id` or `integration_user_name` values fail with `Update Set apply request contains non-JSON value` before candidate planning, integration-user lookup, current Update Set preference changes, dictionary/form upserts, customer-update fetch, or apply result reporting.

Direct Update Set apply change identifiers require exact strings. Corrupted in-process `CandidateChange.table` or `CandidateChange.operation` values fail with `Update Set apply change identifier contains non-JSON value` before custom dictionary discovery, table routing, operation checks, candidate field normalization, integration-user lookup, current Update Set preference changes, dictionary/form upserts, customer-update fetch, or apply result reporting.

Direct Update Set apply change collections are exact-list guarded before routing or dictionary discovery. The apply path accepts only an exact Python list containing exact `CandidateChange` records. List subclasses, alternate iterables, malformed entries, or corrupted in-process model copies fail with `Update Set apply changes contain non-JSON value` before truthiness checks, iteration, table routing, candidate field normalization, integration-user lookup, current Update Set preference changes, dictionary/form upserts, customer-update fetch, or apply result reporting can execute caller-controlled hooks.

Direct Update Set apply change field containers require exact dictionaries with exact string keys before dictionary normalization, form planning, XML attribute parsing, or dictionary upsert payload construction. Dict subclasses, mapping-like objects, malformed field keys, string-subclass field keys, or corrupted in-process `CandidateChange.fields` values fail with `Update Set apply change fields contain non-JSON value` before `.get()`, `.items()`, `dict()`, alias copying, table routing side effects, integration-user lookup, current Update Set preference changes, dictionary/form upserts, customer-update fetch, or apply result reporting can execute caller-controlled hooks.

Direct Update Set apply ServiceNow record collections require exact lists of exact dictionaries. Malformed `fetch_table_records()` responses, list subclasses, mapping-like records, or dict subclasses fail with `Update Set apply records contain non-JSON value` before section-count checks, form-element iteration, shifted-element planning, customer-update truthiness checks, result count calculation, or apply result reporting can execute response-controlled hooks.

Direct Update Set apply ServiceNow single-record lookups require exact dictionaries when a record is found. A missing integration user may still return `None`, but malformed `fetch_table_record()` responses, mapping-like records, or dict subclasses fail with `Update Set apply record contains non-JSON value` before integration-user `sys_id` lookup, current Update Set preference changes, dictionary/form upserts, customer-update fetch, or apply result reporting can execute response-controlled hooks.

Admin diagnostic surfaces redact common secret-bearing text before returning runtime errors.
The JSON admin jobs API and HTML admin console mask URL passwords and sensitive query values
such as `access_token`, `client_secret`, and `signature`. This is a safety boundary for
operator diagnostics, not permission to store secrets in errors, work notes, artifacts, prompts,
or model responses.

ServiceNow API diagnostic redaction uses the same shared sensitive-key vocabulary as runtime
diagnostic redaction. ServiceNow request/response diagnostics mask structured keys such as
`api_key`, `api-key`, `x-api-key`, `aws_secret_access_key`, `awsSecretAccessKey`, `awsSessionToken`, `azureClientSecret`, `token`, `signature`, `id_token`, `idToken`, `client_secret`, `clientSecret`, `client-secret`, `x-client-secret`, `private_key`, `privateKey`, `ssh_private_key`, `Cookie`, `Set-Cookie`, `access_token`, and `accessToken` before errors are
raised or requests are sanitized for tests and logs. Plain diagnostic strings inside ServiceNow
response bodies are also redacted for URL passwords, sensitive query parameters, and assignment
patterns such as `api_key=value`, `api-key=value`, `x-api-key=value`, `clientSecret=value`, and `client_secret="quoted value with spaces"`.
ServiceNow diagnostic secret redaction is traversal-bounded for exact dictionaries, exact lists, and exact tuples. Dictionary, list, and tuple subclasses render as `[non-json value]` before `items()`, `len()`, iteration, or subclass hooks can execute.
Wide request or response diagnostic bodies are sampled with bounded iterators and include
`omitted_fields` or `omitted_items` markers, so redaction cannot be forced to inspect every
nested entry before producing a sanitized diagnostic copy. Secret-redaction traversal is also
cycle-safe; repeated active containers render as `[circular reference]` instead of raising a
secondary recursion failure while sanitizing request or response diagnostics.
Secret-redaction dictionary truncation markers are also collision-safe, so a user-provided
`__jedi_response_truncated__` key remains visible and the internal marker receives a deterministic
duplicate suffix.
ServiceNow diagnostic secret redaction treats text values as untrusted response material and
accepts only exact `str` instances for diagnostic text redaction. String subclasses render as
`[non-json value]` before URL, cookie, Authorization, private-key, or assignment redaction, so
alternate transports cannot inject subclass behavior, object type names, object string output, or
credential-like payloads into sanitized request or response diagnostics. Exact string values are
whitespace/control-character-normalized and capped after diagnostic redaction, and the cap includes
the `...[truncated]` marker, so a sanitized request or response diagnostic copy cannot retain an
oversized text value or raw line-breaking control text.
ServiceNow diagnostic secret redaction also projects object keys before returning sanitized
request or response copies. Exact string keys are redacted and normalized, duplicate rendered keys
receive deterministic suffixes, and non-string keys render as `[non-json key]` without calling
`str()` or `repr()` on the original key. Sensitive-key value masking still uses original exact
string keys, so normal ServiceNow JSON diagnostics preserve structured secret masking while
Python-only diagnostic keys fail closed.
ServiceNow diagnostic secret redaction scalar values are JSON-safe before sanitized request or
response copies are returned. `None`, booleans, integers, finite floats, and exact strings remain
available for diagnostics after redaction. Non-finite floats and unsupported Python objects render
as `[non-json value]` without calling `str()` or `repr()` on the original value.
ServiceNow API error response diagnostics are also whitespace/control-character-normalized before
they are formatted into exceptions, worker failures, artifacts, or ServiceNow work notes. Remote
platform or proxy error strings cannot inject extra diagnostic lines with newline or tab characters.
The final formatted ServiceNow API diagnostic is capped after recursive redaction and normalization,
so a large structured error payload cannot create an oversized exception string even if it did not
come from the default urllib transport.
Sanitized ServiceNow request copies also replace raw
`body_bytes` with a redaction marker so binary attachments or webhook payloads cannot appear in
diagnostic representations. Sanitized request URLs mask URL passwords and sensitive query
parameters while preserving non-sensitive query parameters for operator debugging.
Diagnostic strings that include authorization schemes such as `Authorization: Bearer <token>` or
`Authorization: Basic <token>` preserve the scheme for debugging while redacting the credential.
Diagnostic URL redaction masks the entire URL userinfo component, including username-only
userinfo such as `https://api-token@example.gov/path` and username/password userinfo such as
`https://user:password@example.gov/path`. Malformed diagnostic URLs that cannot be safely
reconstructed are replaced with a redaction marker instead of surfacing parser errors or leaking
URL userinfo.

Exception diagnostic formatting is centralized in `jedi_devproject.exception_diagnostics`. Runtime
handler wrappers, core worker failure persistence, runtime-worker maintenance logging, alert
failure logging, and CLI error rendering use the same bounded fallback behavior for malformed
exception objects. Normal exception strings still flow into the appropriate redaction layer, while
unstringifiable exceptions receive a safe `<subject> raised unstringifiable <ExceptionType>` or
generic `<subject> raised unstringifiable exception` message.
Shared sensitive-key matching fails closed for malformed key objects. If a caller supplies a non-exact string key, the shared classifier treats it as non-sensitive without invoking object stringification or string-subclass methods, so diagnostic redaction paths cannot crash or execute caller-controlled conversion hooks before their own non-string key handling runs.
Sensitive query-key detection decodes percent-encoded key names before matching, so diagnostics
also redact values for encoded keys such as `client%5Fsecret=value` while preserving non-sensitive
query parameters for troubleshooting. Query redaction treats both ampersand-separated and
semicolon-separated parameters as candidates, so `sysparm_limit=1;client%5Fsecret=value` still
masks the sensitive value. Sensitive-key matching normalizes hyphenated and underscored spellings,
so `api-key=value`, `api_key=value`, `client-secret=value`, and `client_secret=value` receive the
same redaction treatment across runtime diagnostics, ServiceNow diagnostics, and alert webhook
validation. Common vendor header-style names such as `x-api-key=value` and
`x-client-secret=value` are treated as sensitive in structured payloads, diagnostic assignments,
and URL query parameters.
Common camelCase JSON and query names such as `clientSecret=value`, `accessToken=value`,
`refreshToken=value`, and `idToken=value` are also treated as sensitive aliases.
Cookie-bearing diagnostics are redacted as whole header values. Runtime diagnostics mask
`Cookie: JSESSIONID=value; route=node` and `Set-Cookie: JSESSIONID=value; HttpOnly` through the
end of the diagnostic line while preserving following lines for status or failure context.
PEM private-key blocks are redacted across diagnostic lines. Diagnostics containing
`-----BEGIN PRIVATE KEY-----` through `-----END PRIVATE KEY-----` are replaced with a single
redaction marker while preserving surrounding status and failure context.
Cloud provider credential names such as `aws_secret_access_key=value`,
`awsSecretAccessKey=value`, `awsSessionToken=value`, and `azureClientSecret=value` are treated as
sensitive in structured payloads, diagnostic assignments, and URL query parameters.

### Secret Inventory

| Secret | Location | Purpose | Rotation Path |
|---|---|---|---|
| `SERVICENOW_CLIENT_SECRET` | API and worker runtime env | ServiceNow OAuth client credentials for Table API operations | Rotate the ServiceNow OAuth app secret, update runtime env, redeploy API and worker |
| `JEDI_LIFECYCLE_WEBHOOK_SECRET` | API runtime env | HMAC validation for inbound lifecycle events | Generate a new random value, update API env and ServiceNow `x_jedi.lifecycle.webhook.secret`, then redeploy/retest signed webhook calls |
| `x_jedi.lifecycle.webhook.secret` | ServiceNow system property | HMAC signing secret read by the lifecycle Business Rule emitter | Match `JEDI_LIFECYCLE_WEBHOOK_SECRET`; update out of band and do not place the value in bootstrap artifacts |
| `OPENAI_API_KEY` | Worker runtime env | ChatGPT/OpenAI model execution | Rotate in the approved OpenAI project, update worker env, redeploy worker, and run a model smoke story |
| `ANTHROPIC_API_KEY` | Worker runtime env | Anthropic model execution when that adapter is explicitly configured | Rotate in the approved Anthropic account or gateway, update worker env, redeploy worker, and run a model smoke story |
| `JEDI_ADMIN_CONSOLE_PASSWORD` | API runtime env, development only | Local Basic auth for `/admin` during development | Replace with a strong temporary value when needed; do not use with `JEDI_ENVIRONMENT=production` |
| `JEDI_ADMIN_API_TOKEN` | API runtime env | Bearer token for JSON artifact/admin diagnostic API endpoints | Rotate by updating the API env and all approved operator clients |

## ChatGPT Implementation Adapter

`OpenAIResponsesProvider` in `jedi_devproject.openai_provider` is the first ChatGPT/OpenAI adapter boundary for implementation candidate generation. It calls the OpenAI Responses API with strict JSON schema output and returns the existing internal implementation candidate shape.

Model provider prompt payloads are strict JSON before outbound request construction. OpenAI and
Anthropic adapters share the same implementation-payload serializer so their user prompt content
stays byte-identical. If a payload contains non-finite numeric values, provider generation fails
before transport send with `Model provider prompt payload contains non-finite numeric values`.
The diagnostic does not echo payload field names, values, or credential-like fragments.

The model-facing schema requires ServiceNow field mutations as explicit `name/value` pairs. The adapter normalizes those pairs into the internal `fields` dictionary after parsing. Arbitrary field objects fail closed at the provider boundary so model output cannot bypass the implementation packet and writeback validators.

Provider candidate normalization is shared across OpenAI and Anthropic adapters and bounded after
JSON parsing. The root provider candidate and all nested response containers are validated before
normalization work begins. The candidate root object, each change object, and each field entry object
must be exact JSON-native dictionaries; `changes` and change `fields` must be exact JSON-native lists.
Nested model-response collections must use exact JSON-native `list` or `dict` containers before length checks, mapping lookups, iteration, copying, or normalization proceeds.
Provider candidates must include at least one change. Empty provider change lists fail with
`response must include at least one change` after root text-list validation, so malformed
`test_plan` and `rollback_notes` diagnostics retain their existing priority.
OpenAI structured-output schema advertises the same provider bounds enforced by the shared
normalizer where JSON Schema supports them: at most 100 changes, at most 100 fields per change,
200-character table and field-name caps, 100000-character string field-value caps,
2000-character rationale caps, and 100-item/2000-character root review-list caps. OpenAI structured-output schema also advertises the numeric safe range
`-9007199254740991..9007199254740991` for provider field values. Anthropic still strips unsupported schema constraints before sending its structured-output schema, so the shared
normalizer remains the authoritative enforcement point for Anthropic and for offline provider
response validation.
OpenAI structured-output schema advertises the safe identifier pattern
`^[A-Za-z_][A-Za-z0-9_]*$` for provider change table and field names. Anthropic strips the `pattern` constraint along with other unsupported structured-output constraints before sending its schema,
so deterministic response normalization remains the authoritative enforcement layer for both
adapters.
OpenAI structured-output schema advertises the provider text policy pattern
`^[^\u0000-\u001F\u007F]*[^\s\u0000-\u001F\u007F][^\u0000-\u001F\u007F]*$` for provider change rationale text and root review-list items.
OpenAI structured-output schema advertises the no-control text pattern plus a non-whitespace
requirement for those same provider text fields; this supersedes the earlier no-control-only pattern
`^[^\u0000-\u001F\u007F]*$`.
Anthropic strips text `pattern` constraints before sending its schema, so deterministic response
normalization remains the authoritative enforcement layer for both adapters.
Provider safe identifier enforcement uses the exported pattern constant
`PROVIDER_SAFE_IDENTIFIER_PATTERN` as the single source for runtime table validation, runtime field
validation, and model-facing schema generation. Do not add parallel hand-coded identifier rules; update
the shared constant and its schema/runtime regression tests together when the ServiceNow identifier
contract changes.
Provider text policy enforcement uses the exported pattern constant
`PROVIDER_NO_CONTROL_TEXT_PATTERN` as the single source for runtime rationale validation, runtime
review-list item validation, and model-facing schema generation. Runtime diagnostics still distinguish
default control-character failures from other future text-policy failures without echoing submitted
text.
Provider text policy requires at least one non-whitespace, non-control character whenever optional
text is supplied as a string. For absent change rationale, use `null` rather than an empty string.
Shared provider system prompt sentence boundaries are regression-tested. The Business Rule metadata
guidance and Catalog Item guidance must remain separated as `script. For standard Catalog Item builds`;
`script.For standard Catalog` is a rejected prompt regression because both adapters send this shared
prompt verbatim.
Object keys on the root candidate, each change object, and each field entry must be exact strings
before lookup, copying, or normalized output. String-subclass keys and non-string keys fail with
fixed diagnostics such as `response candidate keys must be exact strings`,
`response change keys must be exact strings`, or `response field entry keys must be exact strings`.
The same objects also enforce the provider schema's `additionalProperties: false` contract. The root candidate may only include `changes`, `test_plan`, and `rollback_notes`; change objects may only
include `table`, `operation`, `fields`, `sys_id`, and `rationale`; field entries may only include
`name` and `value`. Unknown properties fail with fixed diagnostics such as
`response candidate includes unsupported properties`, `response change includes unsupported properties`,
or `response field entry includes unsupported properties` without echoing the unsupported key or value.
Change metadata is validated after field normalization so field-specific diagnostics retain priority.
Each change must include an exact-string `table`, an exact-string `operation` in `insert`, `update`,
or `delete`, a null `sys_id`, and a `rationale` that is either an exact string or null. Missing or
unsafe metadata fails with fixed diagnostics such as `response change table must be an exact string`,
`response change operation is unsupported`, `response change sys_id must be null`, or
`response change rationale must be an exact string or null` without echoing model-provided metadata.
Provider change table identifiers must be non-empty, contain no whitespace or control characters,
contain at most 200 characters, and use ServiceNow-safe identifier syntax: ASCII letters,
digits, and underscores, starting with a letter or underscore. Provider change rationale text may
be null or a non-empty exact string of at most 2000 characters. Unsafe table identifiers fail with fixed diagnostics such as
`response change table must be a non-empty identifier`,
`response change table must not contain whitespace or control characters`, or
`response change table exceeds 200 characters`; punctuation-bearing or digit-leading table names
fail with `response change table must be a safe identifier`. Provider change table identifiers must use ServiceNow-safe identifier syntax to keep model output aligned with platform table names such as `sys_dictionary`, `cmdb_ci`, and scoped app tables. Oversized rationale text fails with
`response change rationale exceeds 2000 characters`.
Provider change rationale text must not contain ASCII control characters. Ordinary sentence text
with spaces remains accepted, but newline/control-bearing rationale text fails with
`response change rationale must not contain control characters` before normalized artifacts,
operator diagnostics, or ServiceNow work-note planning can consume it.
Provider change field identifiers must use ServiceNow-safe identifier syntax:
ASCII letters, digits, and underscores, starting with a letter or underscore. Field names remain
non-empty, exact strings with no whitespace or control characters and at most 200 characters.
Punctuation-bearing or digit-leading field names fail with
`response field entry name must be a safe identifier` before insertion into normalized fields.
Field entries must include an explicit `value` key, and values must be exact JSON scalar values:
`str`, `bool`, `int`, finite `float`, or `null`. Missing values fail with
`response field entry must include value`; object values, container values, string subclasses,
integer subclasses, non-finite floats, and other non-JSON values fail with
`response field value must be a JSON scalar` before insertion into normalized fields.
Exact string field values may contain at most 100000 characters. Oversized string field values fail
closed with `response field value exceeds 100000 characters` before insertion into normalized
fields, artifacts, work notes, or downstream validators.
Numeric field values must stay within the interoperable safe JSON range
`-9007199254740991..9007199254740991`. Exact integers and finite floats outside that range fail
closed with `response field numeric value is outside safe JSON range` before insertion into
normalized fields. This keeps provider output stable across Python, JSON serialization,
JavaScript-like review tooling, and ServiceNow transport handling.
Root-level provider `test_plan` and `rollback_notes` values are validated after change normalization
so specific change diagnostics retain priority. Both fields must be exact lists, and every item must
be a non-empty exact string, before the normalized candidate is returned. Root-level provider review-list items must be non-empty exact strings; blank or whitespace-only items fail with diagnostics such as
`response test_plan items must be non-empty exact strings` or
`response rollback_notes items must be non-empty exact strings`. Each list may contain at most 100
items, and each item may contain at most 2000 characters. Oversized root text lists fail with
diagnostics such as `response test_plan includes too many items (max 100)` or
`response rollback_notes item exceeds 2000 characters` before artifact or diagnostic creation.
Root-level provider review-list items must not contain ASCII control characters. Ordinary sentence
items with spaces remain accepted, but newline/control-bearing review-list text fails with fixed
diagnostics such as `response test_plan items must not contain control characters` or
`response rollback_notes items must not contain control characters` before normalized artifacts,
operator diagnostics, or ServiceNow work-note planning can consume the items.
Missing fields, list subclasses, and
non-list values fail with `response test_plan must be an exact list` or
`response rollback_notes must be an exact list`; string subclasses and non-string items fail with
`response test_plan items must be exact strings` or
`response rollback_notes items must be exact strings`.
The root candidate check runs before the normalizer reads `changes`, so dictionary subclasses cannot
execute custom lookup hooks. Nested containers are also rejected before length checks, mapping lookups,
iteration, copying, or field normalization. Container subclasses and non-container values fail with
exact-container diagnostics such as `response candidate must be an exact object`,
`response changes must be an exact list`, and `response field entry must be an exact object`, without
echoing model-provided values. A successful model response may contain at most 100 candidate changes
and at most 100 field entries per change before normalization into the internal dictionary shape. Larger candidate responses
fail closed with fixed diagnostics, so a model cannot force oversized post-parse normalization work
or produce an oversized implementation candidate before deterministic validators run.

Provider field names are also validated before `name/value` pairs are collapsed into the internal
field dictionary. Field entry names must be non-empty exact strings, unique within a change, no longer than 200 characters, and free of whitespace or control characters. String subclasses and
non-string values fail with `response field entry must include a non-empty exact name` before emptiness checks, length checks, character scanning, or dictionary-key insertion. Duplicate or unsafe
field names fail closed with fixed diagnostics that do not echo the model-provided field name or value.

The generic provider-policy validator used by `generate_with_provider()` enforces the same 100-change
model-response cap before checking table, operation, and sys_id allowlists. Change `table`,
`operation`, and non-null `sys_id` values must be exact strings before allowlist checks or diagnostic
rendering. String subclasses and non-string values fail with `table must be an exact string`,
`operation must be an exact string`, or `sys_id must be an exact string` before any string conversion
or comparison. Rejected exact-string table, operation, and sys_id diagnostics are redacted,
whitespace/control-character-normalized, and capped before being raised as `ModelResponseError`, so
unsafe model metadata cannot inject log lines or echo secret-like fragments while preserving short operator-useful values such as `sys_user`.
Provider-policy block diagnostics are sanitized the same way before `ProviderBlocked` is raised.
Configured provider ids and requested task names are redacted, whitespace/control-character-normalized,
and capped before inclusion, and prompt construction still does not occur when policy blocks the
task or story data class.

Implementation-packet validation diagnostics are sanitized at model-response decision boundaries.
Unsupported safety decisions and model-proposed table names that do not match the assessed
capability are redacted, whitespace/control-character-normalized, and capped before inclusion in
`ModelResponseError`. Model-proposed table names must be exact strings before capability matching;
string subclasses and non-string table values fail with `model response table names must be exact strings`
before trimming, table comparison, or diagnostic rendering. Raw XML rejection diagnostics remain fixed strings
and do not echo model payloads.

Raw XML validation in implementation-packet responses is traversal-bounded before recursive-looking
model content is accepted. The scanner fails closed when a response exceeds 1,000 scanned nodes or
32 nested levels, and fixed diagnostics are raised without echoing the rejected model payload.
Provider response object keys encountered during the raw XML scan must be exact strings. Non-string
keys and string subclasses fail with `model response object keys must be exact strings` before key
normalization, raw XML field-name comparison, or recursive descent. Raw XML content scanning also
uses exact strings only, so string subclasses cannot execute custom string methods during XML token
checks.

Implementation-packet response contracts enforce bounded review material before candidate
construction. Model responses may contain at most 100 changes, at most 100 `test_plan` items, and
at most 100 `rollback_notes` items. Review items must be non-empty exact strings no longer than 2,000
characters and must not contain control characters. String subclasses and non-string values
fail with `test_plan items must be non-empty exact strings` or
`rollback_notes items must be non-empty exact strings` before any string methods are called.
Violations fail closed with fixed diagnostics that do not echo rejected note content.

Manual-review automation feedback is sanitized before it becomes candidate reviewer notes. Structured
`operator_feedback` entries are accepted only when they are strings; non-string values are skipped
instead of coerced with `str()`. Feedback and suggested-story text is redacted, whitespace/control
characters are collapsed, and each feedback note is capped at 2,000 characters including the
truncation marker.

Unsupported surface-operation eligibility reasons are sanitized before they are written to candidate
artifacts or ServiceNow work notes. Surface operation `kind` and `reason_codes` values are treated as
untrusted packet metadata: string values are redacted, whitespace/control characters are collapsed,
and each value is capped at 2,000 characters including the truncation marker. Non-string reason
codes are skipped instead of coerced with `str()`.

Surface-operation reason generation is collection-bounded. Manual-review candidates include at most
50 unsupported surface-operation entries and at most 50 string reason codes per operation. Additional
unsupported operations or reason codes are represented with fixed omitted-count markers, and malformed
non-list `reason_codes` values are ignored instead of iterated or stringified.

Manual-review ServiceNow work-note feedback is sanitized again at the final writeback boundary.
Eligibility reasons, missing-context names, and actionable reviewer notes are treated as untrusted
candidate metadata: only exact string values are accepted; string subclasses and non-string values are skipped, secret-like fragments are redacted,
whitespace/control characters are collapsed, each emitted value is capped at 500 characters including
the truncation marker, and at most 50 reasons or 50 actionable reviewer notes are included with
omitted-count markers for the rest. This final boundary protects ServiceNow work notes even when a
candidate was assembled outside the normal validated model path.

External build result work notes are sanitized at the writeback planner boundary. Build references
and external build messages are redacted, whitespace/control characters are collapsed, and each value
is capped at 500 characters including the truncation marker before being appended to ServiceNow work
notes. Structured fields such as `u_ai_build_reference` continue to carry the original build
reference for audit correlation and are governed by the structured-field allowlist.

Build-claim work notes sanitize lifecycle event ids at the same writeback planner boundary. Lifecycle
event ids are redacted, whitespace/control characters are collapsed, and capped at 500 characters
including the truncation marker before being appended to the human-readable ServiceNow work note.
Structured build-claim audit events continue to carry the original lifecycle event id for
correlation.

The shared ServiceNow work-note value sanitizer accepts exact strings only. String subclasses and
non-string objects are replaced with a fixed `[non-string work note value]` marker before secret
iteration, diagnostic redaction, whitespace normalization, or truncation can call attacker-controlled
string conversion hooks. CLI summary rendering uses an explicit safe scalar formatter for strings,
booleans, integers, finite floats, and nulls; unsupported values become `[unsupported summary value]`
instead of being coerced with `str()`.
`safe_work_note_value()` treats literal `secret_values` as untrusted even for exact-string work-note
values. Literal secret entries are projected to a bounded exact-string set before replacement;
non-string values, string subclasses, empty values, oversized values, and hostile iterators are
ignored or fail closed without crashing work-note formatting or exposing iterator exception text.

OpenAI provider error diagnostics are redacted and bounded before they can reach worker logs, artifacts, or ServiceNow work notes. Free-form upstream error messages are passed through the shared diagnostic redactor, the configured API key is removed if it appears, and the final provider error message is capped at 4096 characters while preserving structured OpenAI `type` and `code` fields for operator triage. Structured OpenAI `type` and `code` values are also treated as untrusted diagnostic metadata: they are redacted and whitespace/control-character-normalized before inclusion, so upstream metadata cannot inject log lines or echo configured API keys. Provider API error envelopes must be exact dictionaries before diagnostic lookup; dict subclasses fall back to status-only diagnostics, so corrupted transports cannot execute custom lookup hooks while API error messages are being prepared. OpenAI error diagnostic scalar fields must be exact strings before inclusion; message, type, and code string subclasses are ignored so corrupted transports cannot smuggle custom scalar objects into redaction or metadata normalization.

OpenAI successful model output text is bounded before JSON parsing. If a Responses API success
payload contains an `output_text` or `output[].content[].text` value larger than 1,000,000
characters, the adapter fails closed with a fixed diagnostic that names the limit and does not echo
the model output. This prevents malformed or unexpectedly large model responses from creating an
unbounded parse path inside fulfillment workers.

OpenAI and Anthropic successful model output JSON parsing is strict. The provider adapters reject
non-standard JSON numeric constants such as `NaN`, `Infinity`, and `-Infinity` before candidate
normalization, returning the same fixed invalid-JSON diagnostic used for malformed JSON text. The
diagnostic does not echo model-provided field names or values.

OpenAI successful-response text selection is traversal-bounded before JSON parsing. When the
Responses API uses nested `output[].content[]` blocks, the adapter scans only the bounded provider
response collection-item window for both output items and content items. If no `output_text` block
appears in that bounded window, the adapter fails closed instead of walking an arbitrarily wide
successful response.

OpenAI provider settings reject empty `api_key`, `model`, and `base_url` values, reject `api_key` values longer than 4096 characters, reject `model` values longer than 256 characters, reject `base_url` values longer than 2048 characters, and reject those same values when they contain raw or percent-encoded whitespace or control characters before any outbound request can be built. Encoded whitespace/control detection uses a bounded three-pass decode, so double-encoded newline and tab sequences cannot bypass the provider endpoint guard. Provider `base_url` values must be exact strings before URL parsing or endpoint safety checks, must be absolute HTTPS URLs with a hostname, no embedded credentials, no query parameters, and no fragments. Provider `base_url` values must not target local, private, link-local, reserved, multicast, unspecified, delegated `.localhost`, or legacy numeric local targets such as `2130706433`, `0x7f000001`, or `2852039166`. `validate_provider_base_url()` rejects non-exact strings with `base_url must be an exact string`, so direct callers cannot pass nulls, booleans, numbers, bytes, or string subclasses into provider URL safety helpers. `validate_provider_api_key()` and `validate_provider_model()` reject non-exact strings with `api_key must be an exact string` or `model must be an exact string` before length, whitespace, or control-character checks. This keeps direct adapter construction, tests, and future gateway wiring from passing missing or malformed provider credentials, model identifiers, or endpoints into the transport layer.

URL query safety helpers reject non-exact strings before parsing, decoding, sensitive-key matching, or whitespace/control-character checks. Direct callers receive fixed `value must be an exact string` or `query must be an exact string` diagnostics for nulls, booleans, numbers, bytes, or string subclasses, so malformed helper inputs cannot fall through to raw parser errors or subclass behavior while URL guards are preparing production diagnostics. `is_control_character()` rejects malformed direct calls with `character must be an exact string` or `character must be a single character` before looking up the Unicode category, keeping low-level URL helper diagnostics deterministic. The predicate matches every Unicode control, surrogate, and format category (`Cc`, `Cs`, `Cf`, `Cn`), not just ASCII C0 controls, so encoded C1 controls, zero-width spaces, and surrogate sequences are also treated as control characters. `normalize_sensitive_key()` only normalizes exact strings; object-derived values and string subclasses normalize to an empty comparison key before sensitive-key matching. This keeps redaction and query-key checks from invoking arbitrary `__str__`, `strip`, `lower`, or replacement behavior while preparing diagnostics.

Direct OpenAI provider settings validation suppresses rejected input values in Pydantic validation errors. Malformed `base_url` diagnostics still name the `base_url` field, but they do not echo metadata endpoints, embedded credential userinfo, or raw configured URL fragments into worker logs, artifacts, or ServiceNow failure notes.

Anthropic provider error diagnostics follow the same boundary. Free-form upstream Messages API error text is passed through the shared diagnostic redactor, the configured Anthropic API key is removed if it appears, free-form message text is capped before structured metadata is appended, and the final provider error message is capped at 4096 characters while preserving structured Anthropic `type` and `request_id` fields for operator triage. Structured Anthropic `type` values are treated as untrusted diagnostic metadata: they are redacted and whitespace/control-character-normalized before inclusion, so upstream metadata cannot inject log lines or echo configured API keys. Provider API error envelopes must be exact dictionaries before diagnostic lookup; dict subclasses fall back to status-only diagnostics, so corrupted transports cannot execute custom lookup hooks while API error messages are being prepared. Anthropic error diagnostic scalar fields must be exact strings before inclusion; message and type string subclasses are ignored so corrupted transports cannot smuggle custom scalar objects into redaction or metadata normalization. Anthropic response headers must use exact dictionaries before `request-id` or `retry-after` lookup. header subclasses and non-exact header keys or values are ignored, so corrupted transports cannot execute custom header iteration, lowercasing, or value hooks before retry/backoff or error diagnostics. The upstream `request-id` header is treated as diagnostic data, not trusted log text: it is redacted, stripped of control characters, and bounded before being appended to provider errors.

Anthropic successful model output text is bounded before JSON parsing. If the selected text content
block is larger than 1,000,000 characters, the adapter fails closed with a fixed diagnostic that
names the limit and does not echo the model output. This keeps successful-response parsing bounded
independently of API error handling and provider retry policy.

Anthropic successful-response text selection is traversal-bounded before JSON parsing. The Messages
adapter scans only the bounded provider response collection-item window for text content blocks. If
no text block appears in that bounded window, the adapter fails closed instead of walking an
arbitrarily wide successful response.

Provider response JSON text must be exact strings before JSON parsing. OpenAI `output_text`, OpenAI
nested `output[].content[].text`, and Anthropic text content blocks require exact `str` values;
string subclasses are ignored as missing provider output, so corrupted transports cannot execute
custom `__str__` or `__len__` hooks while response text length checks or JSON parsing are being
prepared.
Provider response JSON container lists must be exact lists before traversal. OpenAI `output`, OpenAI
nested `content`, and Anthropic `content` containers require exact `list` values; list subclasses are ignored as missing provider output, so corrupted transports cannot execute custom iterator hooks while
the bounded response scan is being prepared.
Provider response JSON item objects must be exact dictionaries before lookup. OpenAI `output` items,
OpenAI nested `content` items, and Anthropic `content` blocks require exact `dict` values; dict subclasses are ignored as missing provider output, so corrupted transports cannot execute custom
lookup hooks while model output text is being selected.
Provider response content type markers must be exact strings before comparison. OpenAI nested
`output[].content[].type` and Anthropic `content[].type` markers are ignored unless they are exact
strings, so non-string marker objects cannot execute equality hooks while provider output text is
being selected.
Provider response status codes must be exact integers before retry, success, or error branching.
OpenAI and Anthropic adapters reject non-integer status values with fixed diagnostics before
comparison, so status-code objects cannot execute comparison hooks while provider responses are being
classified. Provider response status codes must also be valid HTTP status values in the `100..599`
range; values outside that range are rejected before they can be treated as successful provider
responses or upstream provider failures.
Provider transport responses must be exact response DTOs before any response attributes are read.
OpenAI accepts only exact `HttpResponse` objects. Anthropic accepts exact `HttpResponse` or
`AnthropicHttpResponse` objects. arbitrary response objects cannot execute attribute hooks while
status, headers, or JSON bodies are being selected.
Provider top-level response JSON bodies must be exact dictionaries before provider parsing or API
error diagnostic lookup. response-body subclasses are rejected before provider parsing, so corrupted
or alternate transports cannot execute custom top-level lookup hooks while successful output text or
error details are being selected.
Provider prompt payloads are copied through an exact JSON boundary before serialization. Only exact
JSON containers and scalar values are accepted: exact dictionaries with exact string keys, exact
lists, exact strings, exact numbers, exact booleans, and null. dict subclasses, list subclasses, key subclasses, and scalar subclasses are rejected before `json.dumps`, so caller-supplied payloads
cannot execute custom iteration hooks or be silently normalized into provider prompt JSON.

Provider contract diagnostics do not retain unsafe causes. Prompt payload serialization still fails
with `Model provider prompt payload contains non-finite numeric values` for non-finite numbers and
`Model provider prompt payload contains unsupported JSON value types` for unsupported payload
structures. Strict provider response parsing still maps malformed JSON and non-standard numeric
constants to the adapter's fixed invalid-JSON diagnostic. These public exceptions do not chain the
underlying `TypeError`, `ValueError`, or `JSONDecodeError`, so provider logs, worker failures,
artifacts, and ServiceNow work notes cannot re-expose prompt field names, credential-like payload
fragments, parser offsets, raw response text, or malformed values through `__cause__`.

Anthropic successful-response metadata is also treated as untrusted diagnostic data. Unexpected `stop_reason` values are redacted, stripped of control characters, and bounded before being included in provider exceptions, so malformed model metadata cannot inject log lines, leak the configured Anthropic API key, or create oversized diagnostics. Anthropic successful-response metadata only reflects exact strings. Unsupported metadata values render as `[unsupported provider metadata value]`, so corrupted response adapters cannot execute custom stringification hooks or leak object-provided diagnostics while reporting unexpected `stop_reason` values.

Anthropic retry policy is bounded at provider construction. `AnthropicMessagesProvider` rejects `max_retries` values below zero or above five, preventing accidental unbounded synchronous retry loops from tying up fulfillment workers. Retry delays honor safe finite `retry-after` values up to the configured 30-second provider backoff cap, but padded, whitespace-bearing, control-character-bearing, negative, non-numeric, or non-finite values such as `nan` and `inf` are ignored and fall back to deterministic exponential backoff. Anthropic `retry-after` seconds must parse as ASCII decimal numbers only without signs, underscores, exponent notation, non-ASCII digits, padding, or control characters, so upstream rate-limit headers cannot silently normalize numeric-looking response values into worker sleep durations. Anthropic `max_tokens` is also bounded: provider settings and `ANTHROPIC_MAX_TOKENS` env parsing reject values above 128000 before request construction. `ANTHROPIC_MAX_TOKENS` must parse as ASCII base-10 digits only without signs, underscores, padding, non-ASCII digits, or control characters, so provider configuration cannot silently normalize numeric-looking deployment input.

Anthropic max-token diagnostics do not retain unsafe causes. Malformed `ANTHROPIC_MAX_TOKENS` values still fail with `ANTHROPIC_MAX_TOKENS` must parse as ASCII base-10 digits only, but public `AnthropicProviderConfigError` values do not chain the lower-level strict numeric parser `ValueError`. Startup validation, worker logs, admin diagnostics, alert payloads, and crash reporters therefore cannot re-expose malformed provider environment values or parser details through `__cause__`.

Anthropic provider settings also reject empty `api_key`, `model`, and `base_url` values, reject `api_key` values longer than 4096 characters, reject `model` values longer than 256 characters, reject `base_url` values longer than 2048 characters, and reject those same values when they contain raw or percent-encoded whitespace or control characters before any outbound request can be built. Anthropic env parsing rejects non-empty `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `ANTHROPIC_BASE_URL`, and `ANTHROPIC_MAX_TOKENS` values with leading or trailing whitespace instead of silently trimming them. Encoded whitespace/control detection uses a bounded three-pass decode, so double-encoded newline and tab sequences cannot bypass the provider endpoint guard. Provider `base_url` values must be absolute HTTPS URLs with a hostname, no embedded credentials, no query parameters, no fragments, and no local, private, link-local, reserved, multicast, unspecified, delegated `.localhost`, or legacy numeric local targets. Custom Anthropic gateways remain supported, but credential, model, and endpoint values must be non-empty single-token values suitable for transport construction.

Direct Anthropic provider settings validation follows the same rejected-input suppression boundary. Malformed `base_url` diagnostics name the field without echoing metadata endpoints, embedded credential userinfo, or raw configured URL fragments into operational diagnostics.

Runtime OpenAI use is disabled unless `JEDI_MODEL_PROVIDER=openai` is set. `OPENAI_API_KEY` and `OPENAI_MODEL` must also be present when that provider is enabled. Having `OPENAI_API_KEY` in the host environment does not by itself activate model calls.

`JEDI_MODEL_PROVIDER` env parsing rejects non-empty values with leading, trailing, or internal whitespace/control characters instead of silently trimming them into an active provider selector. Provider selectors are bounded to 256 characters. Blank values still behave as absent and leave model calls disabled.

Direct `RuntimeSettings` wiring follows the same provider-selector boundary. Production validation and worker handler setup reject malformed provider selectors with a fixed `JEDI_MODEL_PROVIDER` diagnostic instead of echoing untrusted selector text into startup errors, worker logs, or ServiceNow failure notes. Unsupported provider selectors also use a fixed `Unsupported JEDI_MODEL_PROVIDER` diagnostic, so arbitrary unsupported selector text is not reflected into diagnostics.

OpenAI env parsing rejects non-empty `OPENAI_API_KEY` and `OPENAI_MODEL` values with leading or trailing whitespace instead of silently trimming them. Those values must also pass the same provider setting guards used by direct adapter construction: non-empty, bounded, and free of whitespace or control characters before runtime settings can be returned.

Worker-side OpenAI provider construction also wraps direct provider setting validation failures as `RuntimeConfigError` values that name only the malformed runtime setting, such as `OPENAI_API_KEY` or `OPENAI_MODEL`. This prevents malformed direct `RuntimeSettings` wiring from surfacing raw provider validation diagnostics or configured provider values in worker failures.

Runtime OpenAI provider runtime diagnostics do not retain unsafe causes. Worker-side OpenAI provider construction still raises diagnostics with the fixed `Invalid OpenAI provider runtime settings:` prefix, including `Invalid OpenAI provider runtime settings: OPENAI_API_KEY` and `Invalid OpenAI provider runtime settings: OPENAI_MODEL`, for malformed direct `RuntimeSettings` values, but the public `RuntimeConfigError` does not chain the original Pydantic `ValidationError`. Worker startup failures, job diagnostics, admin views, alert payloads, and crash reporters therefore cannot re-expose configured provider values, validation metadata, or malformed input fragments through `__cause__`.

When OpenAI runtime mode is enabled, fulfillment first runs the guarded build-claim path, then `model_candidate_fulfillment_handler` builds an `instance_context_bundle`, builds a structured `context_dossier` inside the `implementation_packet`, calls `OpenAIResponsesProvider` only when required context is sufficient, validates the model response, and returns DB-ready JSON artifacts for the context bundle, implementation packet, and implementation candidate. The worker stores those artifacts in `artifact_blobs`, records DB-backed `artifact_refs`, and writes a ServiceNow work note keyed to the fulfillment job id. The model stage does not apply model-generated platform changes.

Model fulfillment artifact payload conversion is strict JSON. `_model_artifact_payload()` preflights
the Python-mode Pydantic model payload with strict JSON numeric handling before returning the
DB-ready JSON-mode artifact shape. If corrupted in-process context bundles, implementation packets,
or implementation candidates contain `NaN`, `Infinity`, or `-Infinity`, artifact payload conversion
fails with `model fulfillment artifact payload contains non-finite numeric values`. The diagnostic
does not echo candidate field names, generated values, story identifiers, or payload values.
Unsupported non-JSON model fulfillment artifact values fail with
`model fulfillment artifact payload contains non-JSON values`; model artifact conversion does not
call `str()` or `repr()` on unsupported objects, bytes, or custom scalar values before DB-ready
artifact payloads are returned. Model fulfillment artifact payload keys and text values must be
exact strings; string subclasses fail with the same non-JSON diagnostic before DB-ready artifact
payloads are returned. Model artifact payload traversal accepts only exact dictionaries, lists, and
tuples; dictionary, list, and tuple subclasses fail before `items()`, iteration, or DB-ready payload
return.

Model fulfillment artifact payload diagnostics do not retain unsafe causes. Non-finite model
artifact payloads still fail with `model fulfillment artifact payload contains non-finite numeric
values`, and unsupported model artifact payload structures still fail with
`model fulfillment artifact payload contains non-JSON values`, but those public `ValueError`
instances do not chain lower-level Pydantic, validation, or JSON encoder exceptions. This keeps
durable artifact persistence, tracebacks, and work-note/report serialization from re-exposing
candidate field names, generated values, story identifiers, object type names, credential-like keys,
or malformed values through `__cause__`.

Implementation packet nested DTO payload conversion is strict JSON. `_packet_model_payload()`
preflights Pydantic DTO payloads used inside implementation packets with strict JSON numeric
handling before the packet is returned for provider prompting or artifact persistence. If corrupted
in-process capability assessments, normalized intents, surface-operation plans, or instance context
DTOs contain `NaN`, `Infinity`, or `-Infinity`, packet construction fails with
`implementation packet nested payload contains non-finite numeric values`. The diagnostic does not echo assessment fields, story identifiers, generated values, or payload values.
Unsupported non-JSON nested DTO values fail with `implementation packet nested payload contains non-JSON values`; nested packet payload conversion does not call `str()` or `repr()` on unsupported
objects, bytes, or custom scalar values before provider prompting or artifact persistence.
Implementation packet nested DTO payload keys and text values must be exact strings; string
subclasses fail with the same non-JSON diagnostic before provider prompting or artifact persistence.
Nested implementation packet payload traversal accepts only exact dictionaries, lists, tuples, sets,
and frozensets; dictionary, list, tuple, set, and frozenset subclasses fail before `items()`,
iteration, provider prompting, or artifact persistence.

Implementation packet raw normalized-intent payloads are strict JSON too. `_packet_raw_payload()`
preflights already-normalized intent dictionaries before they are attached to implementation
packets. If a corrupted in-process automation intent contains `NaN`, `Infinity`, or `-Infinity`,
packet construction fails with `implementation packet raw payload contains non-finite numeric
values`. The diagnostic does not echo normalized-intent field names, operator feedback, story
identifiers, or payload values. Unsupported non-JSON raw normalized-intent payload values fail with
	`implementation packet raw payload contains non-JSON values`; raw payload conversion does not call
	`str()` or `repr()` on unsupported objects, bytes, or custom scalar values. Raw normalized-intent payload keys and text values must be exact strings; string subclasses fail with the same non-JSON
	diagnostic before they are attached to implementation packets.
Raw normalized-intent boolean and integer values must also be exact JSON scalar types; boolean and
integer subclasses fail with the same non-JSON diagnostic before they are attached to implementation
packets, included in provider context, persisted as artifacts, or written to story diagnostics.
Raw normalized-intent payload traversal accepts only exact dictionaries, lists, and tuples;
dictionary, list, and tuple subclasses fail before `items()`, iteration, packet attachment, provider
context construction, artifact persistence, or story diagnostics.

Normalized-intent catalog UI Policy action tristates are strict before deterministic candidate changes are derived. `_catalog_item_changes_from_normalized_intent()` accepts exact strings `true`, `false`, and `ignore`, plus actual JSON booleans, for catalog UI Policy action `visible`, `mandatory`, and `disabled` values. String subclasses and arbitrary objects fail with the fixed catalog variable rule action diagnostic before stringification, trimming, lowercase normalization, candidate-change construction, downstream XML generation, ServiceNow import planning, or story writeback can execute caller-controlled methods.

Catalog UI Policy rendering values are exact normalized values. `_catalog_ui_policy_changes()` revalidates normalized rule title, condition, action variable, tristate fields, and boolean fields before emitting candidate changes, and rejects malformed downstream dictionaries with fixed diagnostics instead of calling `str()`, `bool()`, or `repr()` on rejected values. This keeps direct renderer calls and future bypasses aligned with the normalized-intent parser boundary.

Normalized-intent catalog UI Policy cleared values are exact booleans before deterministic candidate changes are derived. `_catalog_item_changes_from_normalized_intent()` accepts missing `cleared` values as `False` and accepts only actual JSON booleans when `cleared` is provided. Arbitrary objects fail with a fixed catalog variable rule action diagnostic before candidate-change construction, downstream XML generation, ServiceNow import planning, or story writeback can execute caller-controlled methods.

Normalized-intent catalog UI Policy reverse_if_false values are exact booleans before deterministic candidate changes are derived. `_catalog_item_changes_from_normalized_intent()` accepts missing `reverse_if_false` values as `True` and accepts only actual JSON booleans when `reverse_if_false` is provided. Arbitrary objects fail with a fixed catalog variable rule diagnostic before candidate-change construction, downstream XML generation, ServiceNow import planning, or story writeback can execute caller-controlled methods.

Normalized-intent catalog client script action text is exact-string only before deterministic candidate changes are derived. `_catalog_item_changes_from_normalized_intent()` accepts only missing values or exact strings for catalog client script action `kind`, `variable`, and `value` fields. String subclasses and arbitrary objects fail with a fixed catalog client script action diagnostic before action validation, JavaScript rendering, candidate-change construction, downstream XML generation, ServiceNow import planning, or story writeback can execute caller-controlled methods.

Catalog client script rendering values are exact normalized values. `_catalog_client_script_changes()` revalidates normalized script name, watched variable, and script type fields before rendering JavaScript or emitting candidate changes, and rejects malformed downstream dictionaries with fixed diagnostics instead of calling `str()` or `repr()` on rejected values. This keeps direct renderer calls and future bypasses aligned with the normalized-intent parser boundary.

Catalog client script customer-update generation also accepts only exact JSON scalar values before
rendering. `catalog_client_script_customer_updates()` rejects scalar subclasses in script names,
types, watched variables, script bodies, and field read/write declarations with
`Catalog Client Script generation field contains non-JSON value` before script validation, XML
generation, ServiceNow import, or story writeback can execute caller-controlled stringification.

Normalized-intent catalog variable set names are exact-string only before deterministic candidate changes are derived. `_catalog_item_changes_from_normalized_intent()` accepts only exact strings in `catalog_variable_sets`, trims ordinary string whitespace, and rejects string subclasses or arbitrary objects with a fixed catalog variable set diagnostic before candidate-change construction, downstream XML generation, ServiceNow import planning, or story writeback can execute caller-controlled methods.

Normalized-intent catalog variable group members are exact-string only before deterministic candidate changes are derived. `_catalog_item_changes_from_normalized_intent()` accepts only exact strings in each catalog variable group `variables` list, trims ordinary string whitespace, and rejects string subclasses or arbitrary objects with a fixed catalog variable group member diagnostic before candidate-change construction, downstream XML generation, ServiceNow import planning, or story writeback can execute caller-controlled methods.

Normalized-intent catalog variable mandatory values are exact booleans before deterministic candidate changes are derived. `_catalog_item_changes_from_normalized_intent()` accepts missing catalog variable `mandatory` values as `False` and accepts only actual JSON booleans when `mandatory` is provided. Arbitrary objects fail with a fixed catalog variable diagnostic before candidate-change construction, downstream XML generation, ServiceNow import planning, or story writeback can execute caller-controlled methods.

Normalized-intent record producer variable mandatory values are exact booleans before deterministic candidate changes are derived. `_record_producer_changes_from_normalized_intent()` accepts missing record producer variable `mandatory` values as `False` and accepts only actual JSON booleans when `mandatory` is provided. Arbitrary objects fail with a fixed record producer variable diagnostic before candidate-change construction, downstream XML generation, ServiceNow import planning, or story writeback can execute caller-controlled methods.

Normalized-intent fulfillment flow attachment flags are exact booleans before deterministic candidate changes are derived. `_catalog_item_changes_from_normalized_intent()` accepts missing `fulfillment_flow_attachment_requested` values as `False` and accepts only actual JSON booleans when the flag is provided. Arbitrary objects fail with a fixed catalog item fulfillment flow diagnostic before flow creation/modification checks, candidate-change construction, downstream XML generation, ServiceNow import planning, or story writeback can execute caller-controlled methods.

Normalized-intent text values are exact-string only before deterministic candidate changes are derived. `_optional_intent_text()` accepts missing values as absent and accepts only exact strings for shared catalog item and record producer normalized text fields. String subclasses and arbitrary objects fail with a fixed normalized intent text diagnostic before required-field checks, candidate-change construction, downstream XML generation, ServiceNow import planning, or story writeback can execute caller-controlled methods.

Normalized-intent order values are exact positive integers before deterministic candidate changes are derived. `_optional_intent_order()` accepts missing order values as the caller-provided default and accepts only exact positive integers when an order is provided. Booleans, strings, integer subclasses, non-positive integers, and arbitrary objects fail with a fixed normalized intent order diagnostic before candidate-change construction, downstream XML generation, ServiceNow import planning, or story writeback can execute caller-controlled methods.

Implementation packet payload diagnostics do not retain unsafe causes. Nested DTO payload conversion
still fails with `implementation packet nested payload contains non-finite numeric values` or
`implementation packet nested payload contains non-JSON values`, and raw normalized-intent payload
conversion still fails with `implementation packet raw payload contains non-finite numeric values` or
`implementation packet raw payload contains non-JSON values`. Those public `ValueError` instances do
not chain lower-level Pydantic, validation, or JSON encoder exceptions, so provider prompting,
artifact persistence, work-note generation, and tracebacks cannot re-expose assessment fields,
operator feedback, story identifiers, credential-like fragments, object type names, or malformed
values through `__cause__`.

Context dossier DTO payload conversion is strict JSON as well. `_context_model_payload()` preflights
Pydantic DTO payloads assembled inside the model-facing `context_dossier` before compacting or
returning the dossier. If corrupted in-process discovery or surface context DTOs contain `NaN`,
`Infinity`, or `-Infinity`, dossier construction fails with
`context dossier DTO payload contains non-finite numeric values`. Unsupported non-JSON DTO payload
values fail with `context dossier DTO payload contains non-JSON values`; context dossier conversion does not call `str()` or `repr()` on unsupported objects, bytes, or custom scalar values. Context dossier DTO payload keys and text values must be exact strings; string subclasses fail with the same non-JSON diagnostic before compacting or returning the dossier. Boolean, integer, and finite float payload values must also be exact JSON scalar types; scalar subclasses fail with the same non-JSON diagnostic before JSON serialization. Context dossier DTO traversal accepts only exact dictionaries, lists, and tuples; dictionary, list, and tuple subclasses fail before `items()`, iteration, or subclass hooks can execute. The diagnostic does not echo context field names, ServiceNow evidence values, story identifiers, object type names, object string output, or payload values.

Context dossier DTO diagnostics do not retain unsafe causes. Non-finite DTO payloads still fail with
`context dossier DTO payload contains non-finite numeric values`, and unsupported DTO payload
structures still fail with `context dossier DTO payload contains non-JSON values`, but those public
`ValueError` instances do not chain lower-level Pydantic, validation, or JSON encoder exceptions.
This keeps model-facing context assembly, tracebacks, and artifact-report serialization from
re-exposing ServiceNow evidence values, story identifiers, context field names, object type names,
credential-like keys, or malformed values through `__cause__`.

The model-facing dossier can include read-only XML shape references for the selected ServiceNow surface. These references are structured field/record models, not raw `sys_update_xml` payloads, and the model output contract is `structured_candidate_change_only`. Model responses that include raw XML fields or raw Update Set XML content fail validation.

Direct core model and implementation packet validation suppresses rejected input values in Pydantic validation errors. Story records, project context, provider policy, retrieval citations, candidate changes, candidate scripts, Update Set candidates, run manifests, packet stories, and implementation packets still name invalid fields, but type, enum, and parser failures do not echo rejected story text, model confidence fragments, generated script content, review notes, citation values, packet context, or model-facing contract snippets into logs, artifacts, or ServiceNow work notes.

Direct normalized automation intent and artifact generation validation suppresses rejected input values in Pydantic validation errors. Automation intent DTOs, Business Rule, Client Script, Script Include, UI Policy, catalog item, catalog UI policy, catalog client script, record producer, Flow Designer evidence, and ATF test plan schemas still name invalid fields, but type, enum, parser, extra-field, and validator failures do not echo rejected story contract fragments, generated script bodies, catalog variable names, UI conditions, Flow graph evidence, or ATF candidate details into logs, artifacts, or ServiceNow work notes.

Model intent validator diagnostics do not retain unsafe causes. Catalog and record producer reference qualifier failures still use fixed messages such as `reference qualifier rejected`; catalog UI policy condition failures still use `condition rejected`; and catalog client script action or rendering failures still use `action rejected` or `catalog client script <name> rejected`. Public `ValueError` and `ModelResponseError` values at those boundaries do not chain lower-level validator or Pydantic exceptions. Model feedback, candidate artifacts, ServiceNow work notes, admin diagnostics, alert payloads, and crash reporters therefore cannot re-expose rejected model intent fragments, validator exception payloads, generated script details, or malformed catalog variable values through `__cause__`.

Explicit exception cause regression gate. Every explicit source exception cause must be `from None`. The test suite walks the `src/jedi_devproject` AST and fails if a future `raise ... from <named exception>` or other non-`None` cause is introduced. This preserves the hardening boundary that public/operator diagnostics may keep fixed messages but must not retain lower-level exception objects that can later leak through tracebacks, crash reporters, admin diagnostics, alerts, work notes, or artifact serializers.

Shared generation-field scalar coercion is explicit. `bool_value()`, `string_list()`, `optional_int()`, and `reference_value()` accept only primitive JSON-like scalar values used by supported builders, and reject unsupported Python objects, bytes, containers in scalar positions, and non-finite numbers with `generation field scalar value contains non-JSON value`. These helpers do not call `str()` or `repr()` on unsupported values before Business Rule, Client Script, Script Include, UI Policy, catalog, ATF, dictionary/form, or form-section customer update generation.

Shared generation-field scalar text values require exact strings. String subclasses fail with `generation field scalar value contains non-JSON value` before boolean normalization, list item trimming, integer parsing, reference extraction, or downstream builder-specific XML generation can execute caller-controlled string methods.

Shared generation-field boolean and integer values require exact JSON scalar types. Boolean and integer subclasses fail with `generation field scalar value contains non-JSON value` before boolean normalization, list item trimming, integer parsing, reference extraction, or downstream builder-specific XML generation can execute caller-controlled string conversion.

Shared generation-field list, dictionary, and float values also require exact supported types,
and Decimal values are rejected because they are Python-specific numeric objects rather than
JSON generation-field scalars.
- List subclasses fail before list item iteration.
- dictionary subclasses fail before reference value lookup.
- float subclasses and exact Decimal values fail before string conversion.
All use `generation field scalar value contains non-JSON value` so deterministic builders do not
expose caller-controlled container, numeric, lookup, or stringification hooks in diagnostics,
generated XML, artifacts, work notes, or story feedback.

Shared generation field scalar normalization rejects Decimal values. `bool_value()` and
`optional_int()` fail exact Decimal inputs with `generation field scalar value contains non-JSON
value` before trimming, truth-token comparison, integer parsing, or string conversion. This keeps
the shared builder helpers aligned with JSON-like provider and ServiceNow payloads instead of
accepting Python-only numeric object families.

Shared generation-field slug creation requires exact strings for both the requested value and the
fallback default. `slug()` fails string subclasses with `generation field scalar value contains
non-JSON value` before calling `.strip()`, `.lower()`, regex normalization, or returning the default.
Generated update names for Business Rules, Client Scripts, Script Includes, UI Policies, catalog
items, catalog UI policies, and catalog client scripts therefore cannot execute caller-controlled
string hooks while deriving ServiceNow record names.

Stable generated record sys_id derivation requires exact string name parts. `stable_record_sys_id()`
fails string subclasses and non-string objects with `generation field scalar value contains non-JSON
value` before joining parts, UTF-8 encoding, or SHA-256 hashing. Deterministic ServiceNow record ids
for catalog-family generated records therefore cannot execute caller-controlled conversion hooks or
leak Python type names while deriving stable references.

Direct RAG and public-documentation validation suppresses rejected input values in Pydantic validation errors. Local retrieval documents, retrieval results, public-web access config, and public-web responses still name invalid fields, but enum, type, parser, and bounds failures do not echo rejected documentation domains, retrieved content, public-documentation URLs, response snippets, timeout fragments, or citation payloads into logs, artifacts, or ServiceNow work notes.

Public web transport diagnostics do not retain unsafe causes. `UrllibPublicWebTransport` still reports HTTP failures as `public documentation fetch failed with HTTP <status>` and timeout or URL failures as `public documentation fetch failed`, but the public `PublicWebRetrievalBlocked` errors do not chain lower-level `HTTPError`, `URLError`, or `TimeoutError` exceptions. Runtime logs, RAG artifacts, work notes, API errors, and crash reporters therefore cannot re-expose public documentation URLs, sensitive query fragments, redirect details, timeout internals, or transport exception text through `__cause__`.

Direct operational DTO validation suppresses rejected input values in Pydantic validation errors. Alert payloads, builder maturity evidence, context escalation plans, fulfillment artifact references, persisted artifact references, fulfillment execution results, fulfillment worker results, and stale-job requeue reports still name invalid fields, but type, enum, parser, extra-field, and bounds failures do not echo rejected alert details, job ids, artifact refs, artifact payload snippets, worker error fragments, routing reasons, or stale requeue timestamps into logs, artifacts, or ServiceNow work notes.

Context escalation routing is exact-string only before it can allow model execution. `plan_context_escalation()` reads context sufficiency `status` and `missing_context` entries only when they are exact strings. String subclasses, objects, numbers, and other malformed values are treated as absent without coercion. Unsafe `status` values fail closed to manual review, and unsafe missing-context entries are skipped before `context_insufficient:<surface>` reasons are built, so malformed context evidence cannot execute custom string conversion hooks or accidentally authorize a model call.

Direct discovery and Flow evidence validation suppresses rejected input values in Pydantic validation errors. Discovered table fields, form elements, form sections, instance discovery contexts, ServiceNow surface records, surface context bundles, Flow retrieved node evidence, generated Flow customer updates, Flow build results, Flow graph states, Flow round-trip reports, Flow XML shape evidence records, snapshot evidence records, and Flow XML evidence bundles still name invalid fields, but type, enum, parser, extra-field, and bounds failures do not echo rejected instance metadata, script summaries, surface records, graph node details, XML evidence identifiers, payload snippets, graph hashes, snapshot ids, or round-trip assertion details into logs, artifacts, or ServiceNow work notes.

Direct Update Set and writeback DTO validation suppresses rejected input values in Pydantic validation errors. Update Set apply requests, apply results, planned form layout changes, retrieved Update Set handoff requests and results, external build results, story state mappings, writeback policies, writeback plans, writeback audit events, build-claim audit events, writeback execution requests and results, writeback job records, batch results, capability results, and verification results still name invalid fields, but type, enum, parser, extra-field, and bounds failures do not echo rejected story sys_ids, build references, candidate artifacts, retrieved Update Set ids, instance URLs, audit paths, work notes, actor ids, state values, or verification field values into logs, artifacts, or ServiceNow work notes.

Direct capability, planning, safety, and review DTO validation suppresses rejected input values in Pydantic validation errors. Field/form intents, capability profiles, story capability assessments, intake feedback, surface operations, surface operation plans, allowlist policies, eligibility results, review settings, review events, review results, repointing suggestions, and run metrics still name invalid fields, but type, enum, parser, extra-field, and bounds failures do not echo rejected field labels, placement directives, capability names, unsupported cases, operator feedback, suggested stories, surface targets, allowlist values, eligibility reasons, reviewer ids, review reasons, prioritization evidence, or run metrics into logs, artifacts, or ServiceNow work notes.

Capability assessment diagnostics do not retain unsafe causes. Intake feedback content hashes still fail with `intake feedback hash payload contains non-finite numeric values` or `intake feedback hash payload contains non-JSON values` when corrupted guidance, reason, or suggested story payloads are not strict JSON. Automation intent payload conversion still fails with `automation intent payload contains non-finite numeric values` or `automation intent payload contains non-JSON values` for corrupted structured intent payloads. These public `ValueError` instances do not chain lower-level Pydantic, validation, or JSON encoder exceptions, so intake feedback artifacts, work-note generation, capability assessments, and tracebacks cannot re-expose operator feedback, suggested stories, field labels, credential-like fragments, object type names, or malformed values through `__cause__`.

Direct runtime and control-plane DTO validation suppresses rejected input values in Pydantic validation errors. Container smoke plans, external build pipeline results, rate-limit decisions, lifecycle webhook responses, runtime worker summaries, runtime worker settings, build-claim fulfillment config, model fulfillment config, resolved fulfillment flows, dictionary/form intents, Anthropic HTTP responses, CI/CD Update Set probes, pipeline inputs, pipeline results, and artifact handoff plans still name invalid fields, but type, enum, parser, extra-field, and nested-model failures do not echo rejected event payloads, build references, retry decisions, webhook actions, runtime settings, provider policies, flow identifiers, dictionary placement values, provider response details, CI/CD probe output, pipeline artifacts, or delivery handoff evidence into logs, artifacts, or ServiceNow work notes.

Direct bootstrap, enrichment, and risk DTO validation suppresses rejected input values in Pydantic validation errors. Bootstrap field specs, bootstrap field plans, bootstrap apply results, lifecycle webhook bootstrap specs, lifecycle webhook apply and verification results, Update Set importer bootstrap specs, Update Set importer apply results, story enrichment results, and risk inputs still name invalid fields, but type, parser, and nested-model failures do not echo rejected bootstrap field values, lifecycle endpoint details, generated business-rule scripts, retrieved update-set importer scripts, story enrichment payloads, or risk flags into logs, artifacts, or ServiceNow work notes. A project-wide Pydantic DTO audit must report zero `BaseModel` classes without `hide_input_in_errors`.

Before model generation, the worker investigates the target ServiceNow surface. This is broader than table/form metadata. Depending on story signals, the `instance_context_bundle` can include table schema, form layout, Business Rules, Client Scripts, UI Policies, Flow Designer records, Script Includes, ACL indicators, CMDB/discovery indicators, CMDB IRE identification and reconciliation context, outbound REST integration surfaces, and public documentation context.

Dictionary/form discovery metadata is exact-string only before it enters `instance_context_bundle`.
When `discover_dictionary_form_context()` reads `sys_db_object`, `sys_dictionary`, `sys_ui_section`,
`sys_ui_element`, and ACL indicator records, table labels, field names, labels, section ids, section
names, captions, element ids, element names, and ACL operation/name values must be exact strings or
missing. Unsupported objects, bytes, containers, string subclasses, and unstringifiable values fail
with `dictionary/form discovery metadata contains non-JSON value` before table schema, form layout,
or ACL context is persisted or sent to a model.

Dictionary/form discovery numeric metadata is strict as well. Dictionary `max_length` values and form
element `position` values are accepted only as exact integers or digit-only exact strings. Booleans,
numeric subclasses, objects, containers, non-digit strings, and unstringifiable values fail with
`dictionary/form discovery numeric metadata is unsafe` before integer conversion, table schema
context, or form layout context is created.

Dictionary/form discovery record collections are exact containers before context assembly. `discover_dictionary_form_context()` requires `fetch_table_records()` responses for `sys_db_object`, `sys_dictionary`, `sys_ui_section`, `sys_ui_element`, and `sys_security_acl` to be exact lists containing exact dictionaries. List subclasses and record dictionary subclasses fail with `dictionary/form discovery metadata contains non-JSON value` before truthiness checks, indexing, record iteration, `.get()` access, table schema extraction, form-layout extraction, ACL indicators, context dossier persistence, or model invocation can execute caller-controlled container hooks.

Discovery active-state metadata is strict across ServiceNow surface discovery. Record `active`
values are accepted only as exact booleans or exact strings such as `true`, `false`, `1`, `0`, `yes`,
and `no`. Objects, containers, numbers, booleans hidden behind subclasses, string subclasses, and
unstringifiable values fail with `discovery active metadata is unsafe` before surface records,
flow graph context, catalog context, or discovery-map context are created.

Shared ServiceNow surface discovery text metadata is exact-string only. Record names, summaries,
display/reference values, endpoint strings before URL redaction, and selected reference metadata
values accept only exact strings or exact reference dictionaries whose `display_value` and `value`
members are exact strings. String subclasses, object values, dict subclasses, nested containers,
numbers, bytes, and unstringifiable values fail with `discovery text metadata contains non-JSON value`
before model context records, citations, or metadata summaries are created.

Shared ServiceNow surface discovery record collections are exact containers before surface context assembly. `_table_surface()` and `_records_surface()` require fetched or pre-collected ServiceNow records to be exact lists containing exact dictionaries. List subclasses and record dictionary subclasses fail with `discovery text metadata contains non-JSON value` before record iteration, `.get()` access, active-state parsing, name extraction, summary extraction, metadata minimization, citation counts, context dossier persistence, or model invocation can execute caller-controlled container hooks.

Model fulfillment story text for surface context is exact-string only. The worker builds the
surface-discovery and public-documentation query text from `short_description`, `description`, and
`acceptance_criteria` only when those story attributes are exact strings. Missing, non-string,
string-subclass, or unstringifiable values are skipped without coercion, so malformed in-process
story objects cannot execute custom `__str__` hooks or leak story fragments while the worker decides
which ServiceNow context to retrieve.

Model fulfillment story lookup is exact-shape guarded before enrichment, surface discovery, model invocation, retrieved Update Set handoff, or story writeback. `model_candidate_fulfillment_handler()` accepts only exact Python lists containing exact `Story` records from `fetch_stories()`. List subclasses, alternate iterables, model subclasses, and malformed entries fail with `model fulfillment stories contain non-JSON value` before truthiness hooks, indexing hooks, enrichment `model_copy()` hooks, capability analysis, ServiceNow context fetches, provider calls, handoff creation, story mutation, or artifact-return construction can execute caller-controlled behavior.

Model fulfillment required-surface overrides are exact-string only as well. When capability analysis
returns `required_instance_context`, the worker keeps only exact string surface names before passing
the override to live context discovery. Malformed, string-subclass, non-string, or unstringifiable
surface entries are skipped without coercion, so corrupted routing metadata cannot execute custom
`__str__` hooks while deciding which ServiceNow surfaces can unblock model generation.

Persisted fulfillment artifact paths are exact-string only when model fulfillment creates story-facing
artifact references. After packet and candidate artifacts are stored, the worker accepts only exact
string artifact paths such as `db://artifact_blobs/<id>` before creating retrieved Update Set handoff
requests, human-review feedback, or flow preflight references. Missing, non-string, string-subclass,
or unstringifiable persisted artifact paths fail with `persisted artifact path contains non-JSON value`
instead of being coerced with `str()`, so corrupted artifact metadata cannot execute custom conversion
while story work notes or structured AI fields are prepared.

The worker uses read-only Table API retrieval for live instance surfaces. Public documentation retrieval is disabled by default. When `JEDI_PUBLIC_WEB_ACCESS=worker` is set, only the worker can fetch public documentation, and only from `JEDI_PUBLIC_WEB_ALLOWED_DOMAINS` over HTTPS. Public documentation URLs must not include embedded credentials, fragments, whitespace/control characters, encoded whitespace/control characters, or sensitive query parameters such as `token` or `client_secret`, and must not resolve through obvious private-host spellings such as loopback, link-local, reserved, multicast, or legacy numeric local targets. The public-documentation HTTP transport does not follow redirects; any 3xx redirect is blocked before a second outbound request can be made, and post-fetch URL validation still fails closed if an alternate transport reports a different final host. Fetched excerpts are bounded by `JEDI_PUBLIC_WEB_MAX_RESPONSE_BYTES`, `JEDI_PUBLIC_WEB_MAX_EXCERPT_CHARS`, and `JEDI_PUBLIC_WEB_MAX_RESULTS`, stripped of scripts/styles, attached to citations with content hashes, and treated as public documentation context rather than instance truth. Production startup caps those values at `1048576` response bytes, `16000` excerpt characters, and `10` results. When worker public documentation retrieval is enabled, `JEDI_PUBLIC_WEB_TIMEOUT_SECONDS`, `JEDI_PUBLIC_WEB_MAX_RESPONSE_BYTES`, `JEDI_PUBLIC_WEB_MAX_EXCERPT_CHARS`, and `JEDI_PUBLIC_WEB_MAX_RESULTS` must be greater than zero at settings-load time so the worker cannot silently build an empty public-documentation context. If required public documentation cannot be retrieved, the implementation packet records `context_sufficiency.status=insufficient`, the provider is not called, and the story receives human-review or clarification feedback rather than a guessed implementation.

Public-documentation citation versions are exact-string only when live retrieval results are folded
back into model RAG context. If a corrupted in-process retriever result supplies a missing,
non-string, string-subclass, or unstringifiable citation `version`, the worker records an empty
version string instead of coercing it with `str()`. This preserves public-doc evidence without
letting malformed citation metadata execute custom conversion during model context assembly.

Public-documentation citation versions are exact-string only in ServiceNow surface context bundles
as well. When public documentation is represented as the `public_docs` surface inside
`instance_context_bundle`, citation `version` metadata is copied only when it is an exact string.
Missing, non-string, string-subclass, or unstringifiable versions become an empty string before
record metadata or citation dictionaries are persisted. The bundle path does not call `str()` on
malformed public-doc citation versions.

Public-documentation citation `source` and `content_hash` metadata are stricter because they identify
evidence. The `public_docs` surface accepts those citation fields only as exact strings before record
names, metadata, citation dictionaries, or `public_web:<hash>` evidence entries are created.
Missing, non-string, string-subclass, or unstringifiable values fail with
`public documentation citation contains non-JSON value` instead of being coerced.

Public-documentation content excerpts are exact-string only before they become model-facing surface
summaries. The `public_docs` surface rejects missing, non-string, string-subclass, or unstringifiable
retrieved content with `public documentation content contains non-JSON value` before record summaries
or excerpt-length metadata are created. This prevents malformed retriever output from executing custom
conversion while the worker builds `instance_context_bundle`.

Public-documentation query evidence is exact-string only in the same context-bundle path. Query entries
copied into `instance_context_bundle.public_doc_queries` and `public_docs:<query>` evidence strings must
be exact strings. Missing, non-string, string-subclass, or unstringifiable query values fail with
`public documentation query contains non-JSON value` before bundle persistence or model context
assembly.

Public-documentation citation confidence is validated before formatting into model-facing metadata.
The `public_docs` surface accepts only exact integer or float confidence values in the inclusive
`0..1` range. Objects, strings, booleans, subclasses, non-finite numbers, and out-of-range values fail
with `public documentation citation confidence is unsafe` before `__format__` can run while record
metadata or citation dictionaries are created.

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

After a dictionary/form implementation candidate artifact is durably stored, the worker generates reviewed Update Set XML for `JEDI <story number> - AI Candidate` and posts it to the ServiceNow-side importer `jedi_update_set_import`. The XML contains a `sys_remote_update_set` header and candidate customer updates linked through `remote_update_set`, never through a local `update_set`. After import, the worker looks up the retrieved update set by `remote_sys_id`, discovers the active `Ready for Testing` state choice for `rm_story`, and updates the story with `state=<Ready for Testing value>`, `u_ai_status=Ready for Testing`, `u_ai_handoff_type=retrieved_update_set`, `u_ai_handoff_reference=<retrieved update set sys_id>`, `u_ai_artifact_reference=<candidate artifact ref>`, and a work note containing a direct `sys_remote_update_set.do?sys_id=...` link. Retrieved Update Set handoff work-note values are sanitized before formatting: story number, retrieved Update Set name, retrieved Update Set link, and candidate artifact reference are redacted, whitespace/control characters are collapsed, and each value is capped at 500 characters including the truncation marker. Structured handoff fields continue to carry the original references for correlation.

Retrieved Update Set handoff state-choice lookup is exact-shape guarded before state mapping. `_ready_for_testing_state()` accepts only an exact Python list containing exact `StoryStateChoice` records from `fetch_story_state_choices()`. List subclasses, alternate iterables, model subclasses, and malformed entries fail with `retrieved Update Set handoff state choices contain non-JSON value` before iteration hooks, `model_dump()` hooks, Ready-for-Testing mapping construction, story field updates, work-note formatting, or returned handoff metadata can execute caller-controlled behavior. Because this lookup happens after the retrieved Update Set import, operators should inspect the job event stream before retrying a state-choice shape failure.

Retrieved Update Set `remote_sys_id` generation uses only exact string source values. A non-empty exact candidate artifact hash is preferred; otherwise the exact candidate name is used; otherwise a fixed fallback seed is used. Malformed, non-string, or string-subclass hash/name values are skipped before truthiness checks, lowercase conversion, hex filtering, XML serialization, or post-import lookup construction can execute caller-controlled hooks.

This retrieved Update Set is the ServiceNow-native review surface. It is not automatically committed and it does not mutate `sys_dictionary`, `sys_ui_element`, or local `sys_update_set` records during fulfillment. Reviewers must preview, scan, resolve, and commit the retrieved Update Set inside ServiceNow. The story entering Ready for Testing means the automated handoff is ready for human test/review; it does not mean the retrieved Update Set has been approved or committed. `JEDI_UPDATE_SET_APPLY` is retained only as a backward-compatible runtime setting; generated implementation candidates now use the retrieved Update Set handoff path and do not perform local apply-under-update-set mutation.

Retrieved Update Set names require an exact string story number before formatting. Corrupted in-process handoff requests, non-string story numbers, and string subclasses fail with `retrieved Update Set handoff story number contains non-JSON value` before Update Set name construction, XML serialization, ServiceNow import, story work-note formatting, or returned handoff metadata can execute caller-controlled string hooks.

Retrieved Update Set story writeback identifiers require exact string story sys_ids before any import side effects. Corrupted in-process handoff requests, non-string story sys_ids, and string subclasses fail with `retrieved Update Set handoff story sys_id contains non-JSON value` before candidate routing, customer-update generation, XML serialization, ServiceNow import, story field updates, or work-note formatting can execute caller-controlled hooks.

Retrieved Update Set artifact references require exact strings before any import side effects. Corrupted in-process handoff requests, non-string candidate artifact references, and string subclasses fail with `retrieved Update Set handoff artifact reference contains non-JSON value` before candidate routing, customer-update generation, XML serialization, ServiceNow import, structured story field updates, or work-note formatting can execute caller-controlled hooks.

Retrieved Update Set handoff URLs require an exact string instance URL before link construction. Corrupted in-process handoff requests, non-string instance URLs, and string subclasses fail with `retrieved Update Set handoff instance URL contains non-JSON value` before `rstrip()`, story work-note formatting, returned handoff metadata, or downstream API serialization can execute caller-controlled string hooks. The retrieved Update Set may already have been imported by this point, so operators should treat this as a post-import handoff metadata failure and inspect the job event stream before retrying.

Retrieved Update Set handoff change collections are exact-list guarded before routing or description serialization. The handoff accepts only an exact Python list containing exact `CandidateChange` records. List subclasses, alternate iterables, malformed entries, or corrupted in-process model copies fail with `retrieved Update Set handoff changes contain non-JSON value` before truthiness checks, iteration, table routing, customer-update generation, or description summaries can execute caller-controlled hooks.

Retrieved Update Set handoff change identifiers are exact-string guarded before description rendering or builder routing. Candidate change `table` and `operation` values must be exact Python strings. String subclasses and non-string values fail with `retrieved Update Set handoff changes contain non-JSON value` before proposed-change description rendering, string interpolation, table set construction, sorting, deterministic builder selection, dictionary/form intent resolution, customer-update generation, ServiceNow import, or story writeback can execute caller-controlled hooks.

Retrieved Update Set handoff change field containers are exact-dictionary guarded before description rendering or intent extraction. Candidate change `fields` values must be exact Python dictionaries whose keys are exact Python strings. Dictionary subclasses, mapping-like objects, non-string keys, and string-subclass keys fail with `retrieved Update Set handoff change fields contain non-JSON value` before truthiness checks, field iteration, `.items()`, `.get()`, `dict()`, proposed-change summaries, dictionary/form intent extraction, customer-update generation, ServiceNow import, or story writeback can execute caller-controlled hooks.

Retrieved Update Set description headers are sanitized before XML serialization. Story numbers, candidate artifact references, and optional candidate hashes are rendered through the exact-string work-note value boundary: exact strings are redacted, whitespace-normalized, and bounded, while non-string values and string subclasses render as `[non-string work note value]`. This keeps corrupted in-process handoff request data from executing `str()`, `repr()`, or custom string methods while the ServiceNow review artifact is created.

Retrieved Update Set description metrics are serialized through an exact numeric boundary. Candidate confidence and risk score render only when they are exact integers or finite exact floats. Non-finite floats, numeric subclasses, and unsupported metric values render as `[non-json summary value]` before XML serialization, so corrupted in-process candidate metrics cannot execute `str()`, `repr()`, comparison hooks, or custom scalar methods while the review handoff description is created.

Retrieved Update Set descriptions summarize proposed candidate changes through a JSON-safe diagnostic renderer. Exact string summary keys and values are redacted, whitespace-normalized, and bounded; exact booleans, integers, finite floats, and nulls render as simple scalar text. Unsupported summary keys render as `[non-json summary key]`. Unsupported summary values render as `[non-json summary value]` before XML serialization. The description summary path does not call `str()`, `repr()`, or custom scalar hooks on unsupported candidate field values.

Retrieved Update Set reviewer-note collections are exact-list guarded before description serialization. The handoff accepts only an exact Python list for `reviewer_notes`. List subclasses, alternate iterables, and corrupted in-process model copies fail with `retrieved Update Set handoff reviewer notes contain non-JSON value` before truthiness checks or iteration can execute caller-controlled hooks. Individual note values still pass through the work-note sanitizer; non-string notes and string subclasses render as `[non-string work note value]`.

Retrieved Update Set reviewer notes are sanitized before description serialization. Exact string notes are redacted, whitespace-normalized, and bounded with the same work-note value boundary used for story comments. Non-string notes and string subclasses render as `[non-string work note value]` before XML serialization, so corrupted reviewer-note data cannot execute `str()`, `repr()`, or custom string methods while the review handoff description is created.

Retrieved Update Set customer update XML serialization is strict. `import_retrieved_update_set()` accepts only string values for generated customer-update metadata and payload fields before building the `sys_update_xml` unload document. Unsupported Python objects, bytes, containers, numbers, and missing scalar values fail before ServiceNow import with `retrieved Update Set customer update contains non-JSON value`. The XML handoff serializer does not call `str()` or `repr()` on unsupported customer-update values, so object type names, object string output, credential-like fragments, and payload internals are not reflected into retrieved Update Set XML or diagnostics.

Retrieved Update Set import metadata also requires exact strings before unload XML generation. `import_retrieved_update_set()` accepts only exact Python strings for the retrieved Update Set name, `remote_sys_id`, and description. Non-string values and string subclasses fail with `retrieved Update Set metadata contains non-JSON value` before customer update XML generation, XML escaping, ServiceNow import, post-import lookup construction, story work-note formatting, or returned handoff metadata can execute caller-controlled string hooks.

Retrieved Update Set generated customer update collections are exact-shape guarded before handoff emptiness checks and XML generation. `_customer_updates_for_candidate()` and `import_retrieved_update_set()` accept only exact Python lists containing exact dictionaries for generated customer updates. List subclasses, alternate iterables, dictionary subclasses, malformed records, and corrupted builder fixtures fail with `retrieved Update Set customer update contains non-JSON value` before truthiness checks, customer update iteration, field extraction, CDATA escaping, XML assembly, ServiceNow import, or post-import lookup can execute caller-controlled hooks.

Retrieved Update Set customer update text values require exact strings. String subclasses fail with `retrieved Update Set customer update contains non-JSON value` before CDATA escaping, XML attribute escaping, unload document assembly, ServiceNow import, post-import lookup, story field update, or handoff work-note formatting can execute caller-controlled string methods.

Retrieved Update Set post-import lookup handling is strict as well. After XML import, `import_retrieved_update_set()` accepts only primitive string, boolean, and integer scalar values for the returned `sys_remote_update_set.sys_id`. Unsupported objects, bytes, containers in scalar positions, floats, and non-scalar values fail with `retrieved Update Set lookup contains non-JSON value` before URL construction, story field updates, work-note formatting, or downstream handoff reporting. The lookup path does not call `str()` or `repr()` on unsupported ServiceNow response values.

Retrieved Update Set post-import lookup record collections are exact-shape guarded before `sys_id` extraction. The lookup response must be an exact Python list whose first record, when present, is an exact dictionary. List subclasses, alternate iterables, dictionary subclasses, malformed records, and corrupted client fixtures fail with `retrieved Update Set lookup contains non-JSON value` before truthiness checks, indexing hooks, `.get()` hooks, URL construction, story field updates, or work-note formatting can execute caller-controlled behavior. An empty exact list still means the import lookup returned no record and raises `ServiceNow imported Update Set lookup did not include sys_id`.

Dictionary/form retrieved Update Set intent extraction is strict too. Before customer updates are generated, dictionary/form handoff accepts only exact primitive `str`, `bool`, and `int` scalar values for candidate table names, field names, labels, types, default values, reference metadata, max length, mandatory flags, and placement directives. Unsupported objects, bytes, containers, floats, string subclasses, integer subclasses, and other non-scalar values fail with `dictionary/form handoff field contains non-JSON value`. The extraction path does not call `str()` or `repr()` on unsupported candidate fields before validation, XML generation, ServiceNow import, or story writeback.

Dictionary/form handoff candidate field selection is truthiness-safe. The fallback selector that chooses among aliases such as `element`, `field_name`, `column_label`, and `label` treats only exact strings, booleans, integers, and nulls as values with meaningful presence. Unsupported objects are passed to the strict field validator and fail with `dictionary/form handoff field contains non-JSON value` before `__bool__`, `str()`, or `repr()` can execute.

Dictionary/form handoff alias selection is truthiness-safe across table, reference, qualifier, and placement metadata. `_form_table_name()`, `_reference_table()`, `_reference_qualifier()`, `_placement_anchor()`, and `_story_table_name()` select aliases with the same `_first_present()` and `_candidate_field_present()` boundary used by field selection. Unsupported objects fail with `dictionary/form handoff field contains non-JSON value` before boolean chaining, `if` checks, `__bool__`, string conversion, table normalization, reference resolution, placement planning, customer-update generation, ServiceNow import, or story writeback can execute caller-controlled hooks.

Dictionary/form handoff reference table metadata accepts only exact dictionaries before reading nested `value` or `display_value` fields. Dictionary subclasses fail with `dictionary/form handoff field contains non-JSON value` before candidate-derived reference metadata can execute caller-controlled mapping accessors. Exact dictionaries remain supported for structured reference metadata emitted by model/provider normalization.

Dictionary/form live metadata consumption is strict as well. `dictionary_form_customer_updates()` accepts only primitive string, boolean, and integer scalar values from fetched `sys_ui_section` and `sys_ui_element` records when resolving section sys_ids, captions, users, views, element names, element sys_ids, and positions. Unsupported objects, bytes, containers in scalar positions, floats, and non-scalar values fail with `dictionary/form metadata field contains non-JSON value` before anchor matching, view filtering, form layout planning, XML generation, ServiceNow import, or story writeback. The metadata path does not call `str()` or `repr()` on unsupported fetched ServiceNow metadata values.

Dictionary/form metadata text values require exact strings. String subclasses fail with `dictionary/form metadata field contains non-JSON value` before default-view filtering, anchor matching, position normalization, form-layout planning, XML generation, ServiceNow import, or story writeback can execute caller-controlled string methods.

Dictionary/form metadata scalar values require exact JSON scalar types. Boolean and integer subclasses fail with `dictionary/form metadata field contains non-JSON value` before default-view filtering, anchor matching, position normalization, form-layout planning, XML generation, ServiceNow import, or story writeback can execute caller-controlled string conversion.

Dictionary/form reference metadata dictionaries are exact containers. Default-view filtering, view payload serialization, reference-value extraction, and form-layout XML generation accept only exact dictionaries before `value` or `display_value` lookup. Dictionary subclasses fail with `dictionary/form metadata field contains non-JSON value` before retrieved Update Set handoff planning can execute caller-controlled mapping accessors.

Dictionary/form ServiceNow metadata record collections are exact containers. `fetch_table_records()` responses for `sys_ui_section` and `sys_ui_element` must be exact lists containing exact dictionaries. List subclasses and record dictionary subclasses fail with `dictionary/form metadata field contains non-JSON value` before section iteration, default-view filtering, element lookup, anchor matching, form-layout planning, XML generation, ServiceNow import, or story writeback can execute caller-controlled container hooks.

Dictionary/form form-layout XML requires fetched existing `sys_ui_element` rows to include `sys_id`. Missing existing element identifiers fail with `dictionary/form metadata field is missing` before form-layout XML generation, ServiceNow import, or story writeback, so retrieved Update Set payloads cannot silently serialize blank identifiers for existing form rows. Generated inserted field rows may still omit `sys_id` because ServiceNow assigns identifiers when the retrieved update is committed.

Form-section removal customer-update generation also treats candidate fields and discovered section metadata as untrusted scalar inputs. `form_section_customer_updates()` accepts only primitive string, boolean, and integer scalar values for target tables, requested sections, views, captions, sys_ids, and related reference display/value fields. Unsupported objects, bytes, containers, floats, and non-scalar values fail with `form section removal field contains non-JSON value` before metadata lookup, section matching, XML generation, ServiceNow import, or story writeback. The form-section path does not call `str()` or `repr()` on unsupported values.

Form-section removal text values require exact strings. String subclasses fail with `form section removal field contains non-JSON value` before metadata lookup, requested-section normalization, view filtering, section matching, DELETE XML generation, ServiceNow import, or story writeback can execute caller-controlled string methods.

Form-section removal scalar values require exact JSON scalar types. Boolean and integer subclasses fail with `form section removal field contains non-JSON value` before metadata lookup, requested-section normalization, view filtering, section matching, DELETE XML generation, ServiceNow import, or story writeback can execute caller-controlled string conversion.

Form-section removal list and dictionary values are exact containers. `_section_names()` accepts only
exact lists before iterating requested section names, and discovered section reference metadata must
be exact dictionaries before display/value lookup. List and dictionary subclasses fail with `form
section removal field contains non-JSON value` before metadata lookup, section matching, DELETE XML
generation, ServiceNow import, or story writeback can execute caller-controlled container methods.

Form-section removal ServiceNow metadata record collections are exact containers. `fetch_table_records()` responses for `sys_ui_section` must be exact lists containing exact dictionaries. List subclasses and record dictionary subclasses fail with `form section removal field contains non-JSON value` before section iteration, view filtering, section matching, section sys_id resolution, DELETE XML generation, ServiceNow import, or story writeback can execute caller-controlled container hooks.

Form-section removal customer-update generation requires matched `sys_ui_section` records to include `sys_id`. Missing section identifiers fail with `form section removal field is missing` before update naming, DELETE XML generation, ServiceNow import, or story writeback, so retrieved Update Set payloads cannot silently serialize blank section identifiers.

Record producer customer-update generation is strict as well. `record_producer_customer_updates()` accepts only primitive string, boolean, and integer scalar values for producer metadata, target table references, mapped variable fields, and discovered target-table field metadata. Unsupported objects, bytes, containers, floats, and non-scalar values fail with `record producer generation field contains non-JSON value` before target-table validation, metadata lookup, XML generation, ServiceNow import, or story writeback. The record producer path does not call `str()` or `repr()` on unsupported values.

Record producer generation text values require exact strings. String subclasses fail with `record producer generation field contains non-JSON value` before producer metadata parsing, target-table validation, mapped-variable field normalization, XML generation, ServiceNow import, or story writeback can execute caller-controlled string methods.

Record producer generation scalar values are exact JSON scalars.
`_record_producer_field_text()` accepts only exact strings, exact booleans, exact integers, and
nulls; boolean and integer subclasses fail with `record producer generation field contains non-JSON
value` before producer metadata parsing, target-table validation, mapped-variable field
normalization, XML generation, ServiceNow import, or story writeback can execute caller-controlled
stringification.

Record producer ServiceNow metadata record collections are exact containers. Target-table,
dictionary-field, catalog, and category discovery results from `fetch_table_records()` must be exact
lists containing exact dictionaries before target-table existence checks, mapped-field iteration,
catalog resolution, or category matching. List subclasses, alternate collections, mapping-like
records, and dictionary subclasses fail with `record producer generation field contains non-JSON
value` before metadata iteration, record field access, XML generation, ServiceNow import, or story
writeback can execute caller-controlled container methods.

Catalog item customer-update generation treats catalog-facing model output and discovered ServiceNow metadata as untrusted scalar inputs. `catalog_item_customer_updates()` accepts only primitive string, boolean, and integer scalar values for item metadata, variable metadata, variable set names, compact variable group declarations, fulfillment flow names, active flags, display fields, sys_ids, and related reference display/value fields. Unsupported objects, bytes, containers in scalar positions, floats, and non-scalar values fail with `catalog item generation field contains non-JSON value` before catalog/category/topic/flow resolution, metadata lookup, XML generation, ServiceNow import, or story writeback. The catalog item path does not call `str()` or `repr()` on unsupported values.

Catalog item generation text values require exact strings. String subclasses fail with `catalog item generation field contains non-JSON value` before item-name normalization, variable metadata parsing, catalog/category/topic/flow lookup, XML generation, ServiceNow import, or story writeback can execute caller-controlled string methods.

Catalog item customer-update generation requires matched catalog metadata records to include `sys_id`. Missing catalog, category, Employee Center taxonomy/topic/content type, or variable-set identifiers fail with `catalog item metadata field is missing` before relationship XML generation, ServiceNow import, or story writeback, so retrieved Update Set payloads cannot silently serialize blank catalog references.

Catalog item customer-update metadata text accepts only exact JSON scalar values before rendering.
Catalog, category, taxonomy, Employee Center topic, variable-set, and fulfillment-flow metadata from
ServiceNow discovery may provide exact strings, exact booleans, exact integers, or nulls, but scalar
subclasses and arbitrary objects fail with `catalog item generation field contains non-JSON value`
before active record filtering, display matching, relationship XML generation, ServiceNow import, or
story writeback can execute caller-controlled stringification.

Catalog item generation list and dictionary values are exact containers. Variable-set and variable
group declarations accept only exact lists before iteration, variable group mapping entries must be
exact dictionaries before validation, and ServiceNow reference metadata must be exact dictionaries
before display/value lookup. List and dictionary subclasses fail with `catalog item generation field
contains non-JSON value` before catalog/category/topic/flow resolution, metadata matching, XML
generation, ServiceNow import, or story writeback can execute caller-controlled container methods.

Catalog item ServiceNow metadata record collections are exact containers too. Catalog, category,
taxonomy, Employee Center topic, content-type, and variable-set discovery results from
`fetch_table_records()` must be exact lists containing exact dictionaries before catalog resolution
iterates records or reads fields. List subclasses, alternate collections, mapping-like records, and
dictionary subclasses fail with `catalog item generation field contains non-JSON value` before active
record filtering, display matching, sys_id extraction, relationship XML generation, ServiceNow
import, or story writeback can execute caller-controlled container methods.

Catalog and Employee Center surface discovery record collections are exact containers before context
dossier assembly. Employee Center `taxonomy`, `topic`, `taxonomy_content_configuration`, and
`m2m_connected_content` fetch results must be exact lists containing exact dictionaries before topic
iteration, content-type filtering, citation counts, surface records, missing-surface decisions, or
model invocation can execute caller-controlled container hooks. Malformed discovery containers fail
with `discovery text metadata contains non-JSON value`.

Script Include customer-update generation also uses a Script Include-specific scalar boundary. `script_include_customer_updates()` accepts only primitive string, boolean, and integer scalar values for Script Include name, API name, scope, callable/active flags, description, script body, public methods, table access metadata, and field access metadata. Unsupported objects, bytes, containers in scalar positions, floats, and non-scalar values fail with `Script Include generation field contains non-JSON value` before script safety scanning, DTO validation, XML generation, ServiceNow import, or story writeback. The Script Include path does not call `str()` or `repr()` on unsupported values.

Script Include generation text values require exact strings. String subclasses fail with `Script Include generation field contains non-JSON value` before script safety scanning, scope normalization, method extraction, DTO validation, XML generation, ServiceNow import, or story writeback can execute caller-controlled string methods.

Script Include generation scalar values are exact JSON scalars. `_script_include_field_text()` accepts
only exact strings, exact booleans, exact integers, and nulls; boolean and integer subclasses fail
with `Script Include generation field contains non-JSON value` before Script Include names, scope
normalization, callable/active flags, method extraction, script safety scanning, XML generation,
ServiceNow import, or story writeback can execute caller-controlled stringification.

Script Include generation list values are exact containers. `_script_include_string_list()` accepts
only exact lists before iterating public method metadata, table access metadata, or field access
metadata. List subclasses fail with `Script Include generation field contains non-JSON value` before
method extraction, utility-profile validation, script safety scanning, XML generation, ServiceNow
import, or story writeback can execute caller-controlled iterators.

Business Rule customer-update generation uses the same fail-closed posture for executable server-side candidate fields. `business_rule_customer_updates()` accepts only primitive string, boolean, and integer scalar values for target table, rule name, timing, operation aliases, filter conditions, script body, and declared table/field access metadata. Unsupported objects, bytes, containers in scalar positions, floats, and non-scalar values fail with `Business Rule generation field contains non-JSON value` before operation inference, script safety scanning, field-write validation, XML generation, ServiceNow import, or story writeback. The Business Rule path does not call `str()` or `repr()` on unsupported values.

Business Rule generation text values require exact strings. String subclasses fail with `Business Rule generation field contains non-JSON value` before operation inference, timing normalization, script safety scanning, field-write validation, XML generation, ServiceNow import, or story writeback can execute caller-controlled string methods.

Business Rule generation scalar values are exact JSON scalars. `_business_rule_field_text()` accepts
only exact strings, exact booleans, exact integers, and nulls; boolean and integer subclasses fail
with `Business Rule generation field contains non-JSON value` before server-side rule fields,
operation aliases, declared access metadata, script validation, XML generation, ServiceNow import, or
story writeback can execute caller-controlled stringification.

Business Rule generation list values are exact containers. `_business_rule_string_list()` accepts
only exact lists before iterating declared read/write field metadata. List subclasses fail with
`Business Rule generation field contains non-JSON value` before operation inference, script safety
scanning, field-write validation, XML generation, ServiceNow import, or story writeback can execute
caller-controlled iterators.

Client Script customer-update generation applies the same boundary to browser-side executable candidate fields. `client_script_customer_updates()` accepts only primitive string, boolean, and integer scalar values for target table, script name, script type, watched field, script body, declared field access metadata, and user-facing message metadata. Unsupported objects, bytes, containers in scalar positions, floats, and non-scalar values fail with `Client Script generation field contains non-JSON value` before script type validation, script safety scanning, field-write validation, XML generation, ServiceNow import, or story writeback. The Client Script path does not call `str()` or `repr()` on unsupported values.

Client Script generation text values require exact strings. String subclasses fail with `Client Script generation field contains non-JSON value` before script type validation, watched-field validation, script safety scanning, field-write validation, XML generation, ServiceNow import, or story writeback can execute caller-controlled string methods.

Client Script generation scalar values are exact JSON scalars. `_client_script_field_text()` accepts
only exact strings, exact booleans, exact integers, and nulls; boolean and integer subclasses fail
with `Client Script generation field contains non-JSON value` before browser-side script fields,
watched-field validation, declared access metadata, script safety scanning, XML generation,
ServiceNow import, or story writeback can execute caller-controlled stringification.

Client Script generation list values are exact containers. `_client_script_string_list()` accepts
only exact lists before iterating declared read/write field metadata or user-facing message metadata.
List subclasses fail with `Client Script generation field contains non-JSON value` before script type
validation, watched-field validation, script safety scanning, XML generation, ServiceNow import, or
story writeback can execute caller-controlled iterators.

UI Policy customer-update generation now treats declarative form-behavior fields as untrusted scalar inputs as well. `ui_policy_customer_updates()` accepts only primitive string, boolean, and integer scalar values for policy names, target tables, conditions, descriptions, views, flags, order values, action policy names, action tables, action fields, tristate action values, and clear-value flags. Unsupported objects, bytes, containers in scalar positions, floats, and non-scalar values fail with `UI Policy generation field contains non-JSON value` before policy/action matching, tristate validation, forbidden-token scanning, XML generation, ServiceNow import, or story writeback. The UI Policy path does not call `str()` or `repr()` on unsupported values.

UI Policy generation text values require exact strings. String subclasses fail with `UI Policy generation field contains non-JSON value` before policy/action matching, tristate validation, forbidden-token scanning, integer parsing, XML generation, ServiceNow import, or story writeback can execute caller-controlled string methods.

UI Policy generation scalar values are exact JSON scalars. `_ui_policy_field_text()` accepts only
exact strings, exact booleans, exact integers, and nulls; boolean and integer subclasses fail with
`UI Policy generation field contains non-JSON value` before policy names, target tables, action
fields, tristate values, integer parsing, XML generation, ServiceNow import, or story writeback can
execute caller-controlled stringification.

Catalog UI Policy customer-update generation applies the same strict boundary to catalog item form behavior. `catalog_ui_policy_customer_updates()` accepts only primitive string, boolean, and integer scalar values for policy names, catalog item names, catalog conditions, flags, order values, script placeholders, action policy names, action variables, action tristate values, and clear-value flags. Unsupported objects, bytes, containers in scalar positions, floats, and non-scalar values fail with `Catalog UI Policy generation field contains non-JSON value` before policy/action matching, variable ownership checks, condition parsing, tristate validation, XML generation, ServiceNow import, or story writeback. The Catalog UI Policy path does not call `str()` or `repr()` on unsupported values.

Catalog UI Policy generation text values require exact strings. String subclasses fail with `Catalog UI Policy generation field contains non-JSON value` before policy/action matching, variable ownership checks, condition parsing, tristate validation, integer parsing, XML generation, ServiceNow import, or story writeback can execute caller-controlled string methods.

Catalog UI Policy generation scalar values are exact JSON scalars.
`_catalog_ui_policy_field_text()` accepts only exact strings, exact booleans, exact integers, and
nulls; boolean and integer subclasses fail with `Catalog UI Policy generation field contains
non-JSON value` before policy names, catalog conditions, action variables, tristate values, integer
parsing, XML generation, ServiceNow import, or story writeback can execute caller-controlled
stringification.

Catalog Client Script customer-update generation uses a Catalog Client Script-specific scalar boundary for generated browser-side catalog behavior. `catalog_client_script_customer_updates()` accepts only primitive string, boolean, and integer scalar values for catalog item names, script names, script types, watched variables, script bodies, declared fields read, and declared fields written. Unsupported objects, bytes, containers in scalar positions, floats, and non-scalar values fail with `Catalog Client Script generation field contains non-JSON value` before script type validation, script safety scanning, field-write validation, catalog variable ownership checks, XML generation, ServiceNow import, or story writeback. The Catalog Client Script path does not call `str()` or `repr()` on unsupported values.

Catalog Client Script generation text values require exact strings. String subclasses fail with `Catalog Client Script generation field contains non-JSON value` before script type validation, script safety scanning, field-write validation, catalog variable ownership checks, XML generation, ServiceNow import, or story writeback can execute caller-controlled string methods.

Catalog Client Script generation list values are exact containers. `_catalog_client_script_string_list()`
accepts only exact lists before declared read/write field iteration; list subclasses fail with
`Catalog Client Script generation field contains non-JSON value` before script type validation,
script safety scanning, field-write validation, catalog variable ownership checks, XML generation,
ServiceNow import, or story writeback can execute caller-controlled iteration hooks.

Advisory ATF test plan generation now applies the same scalar boundary before deriving review artifacts from candidate changes. `generate_atf_test_plan()` accepts only primitive string, boolean, and integer scalar values for candidate-derived table names, field names, policy names, catalog item names, variable names, conditions, operation flags, and declared field-write metadata. Unsupported objects, bytes, containers in scalar positions, floats, and non-scalar values fail with `ATF test plan generation field contains non-JSON value` before test names, step descriptions, step inputs, not-covered entries, assumptions, or artifact payloads are built. The ATF test plan path does not call `str()` or `repr()` on unsupported candidate fields.

ATF test plan generation text values require exact strings. String subclasses fail with `ATF test plan generation field contains non-JSON value` before operation-flag parsing, scenario detection, step normalization, DTO validation, artifact serialization, ServiceNow import planning, or story writeback can execute caller-controlled string methods.

ATF test plan generation scalar values are exact JSON scalars. `_atf_field_text()` accepts only
exact strings, exact booleans, exact integers, and nulls; boolean and integer subclasses fail with
`ATF test plan generation field contains non-JSON value` before operation-flag parsing, scenario
detection, step normalization, DTO validation, artifact serialization, ServiceNow import planning,
or story writeback can execute caller-controlled stringification.

ATF test plan generation list values are exact containers. `_atf_string_list()` accepts only exact
lists before declared field-write metadata iteration; list subclasses fail with
`ATF test plan generation field contains non-JSON value` before business-rule scenario detection,
step construction, DTO validation, artifact serialization, ServiceNow import planning, or story
writeback can execute caller-controlled iteration hooks.

If the deterministic packet gates produce a non-automated candidate, or if model reasoning succeeds but builder maturity is below the automated handoff threshold, the worker stores the implementation packet and candidate artifacts, writes either `u_ai_status=Needs Clarification` or `u_ai_status=Human Review Required`, writes a story work note with the candidate artifact reference and eligibility reasons, and does not create a retrieved Update Set.

Intake feedback work notes are sanitized before delivery to ServiceNow. Story numbers, reason codes, operator guidance, and suggested rewrites are redacted, whitespace/control characters are collapsed, and each value is capped at 500 characters including the truncation marker. Intake notes include at most 50 reason codes and 50 guidance items, with fixed omitted-count markers for the rest. The durable intake feedback artifact preserves the structured feedback payload for audit correlation.

Intake feedback content hashes are strict JSON. `_intake_content_hash()` serializes the intake
feedback hash payload with strict JSON numeric handling before SHA-256 computation. If corrupted
in-process gate feedback contains `NaN`, `Infinity`, or `-Infinity`, content-hash generation fails
with `intake feedback hash payload contains non-finite numeric values`. The diagnostic does not echo
operator feedback, suggested rewrites, story identifiers, field names, or values, so intake feedback
provenance cannot be minted over Python-only numeric tokens. Unsupported non-JSON feedback hash
values fail with `intake feedback hash payload contains non-JSON values`; intake feedback hashing does not call `str()` or `repr()` on unsupported objects, bytes, or custom scalar values before canonicalization.

Capability assessment automation-intent payloads are strict JSON too. `_automation_intent_payload()`
preflights normalized `AutomationIntent` DTOs before embedding them into `StoryCapabilityAssessment`
artifacts. If corrupted in-process automation intent contains `NaN`, `Infinity`, or `-Infinity`,
assessment construction fails with `automation intent payload contains non-finite numeric values`.
Unsupported non-JSON automation-intent payload values fail with
`automation intent payload contains non-JSON values`; automation-intent payload conversion does not
call `str()` or `repr()` on unsupported objects, bytes, or custom scalar values. Automation-intent payload keys and text values must be exact strings; string subclasses fail with the same non-JSON
diagnostic before assessment construction. Boolean, integer, and finite float automation-intent payload values must also be exact JSON scalar types; scalar subclasses fail with the same non-JSON diagnostic before assessment construction. Automation-intent payload traversal accepts only exact dictionaries, lists, and tuples; dictionary, list, and tuple subclasses fail before `items()`, iteration, or subclass hooks can execute. The diagnostic does not echo intent field names, field
labels, story identifiers, object type names, object string output, or payload values.

Advisory ATF test plan artifacts use the same strict JSON conversion before they are added to
fulfillment artifacts. `_atf_test_plan_artifact()` treats non-finite ATF plan payloads as advisory
generation failures: it logs a redacted warning, omits the ATF plan artifact, and continues the
implementation candidate result. If corrupted in-process ATF plan DTOs contain `NaN`, `Infinity`,
or `-Infinity`, conversion fails with `ATF test plan artifact payload contains non-finite numeric
values`. The diagnostic does not echo step fields, generated ATF values, story identifiers, or
payload values.

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

Flow graph discovery record collections are exact containers before graph context assembly. `resolve_fulfillment_flow()`, `_flow_surfaces()`, and `_fetch_flow_graph_records()` require `sys_hub_flow`, `sys_hub_trigger_instance`, `sys_hub_action_instance`, `sys_hub_flow_logic_instance_v2`, `sys_hub_trigger_input`, `sys_hub_trigger_output`, `sys_hub_action_input`, and `sys_hub_action_output` fetch results to be exact lists containing exact dictionaries. List subclasses and record dictionary subclasses fail with `discovery text metadata contains non-JSON value` before fulfillment-flow matching, graph completeness checks, citation counts, graph record rendering, context dossier persistence, or model invocation can execute caller-controlled container hooks.

Sprint 126 adds validation-only graph diff support for the pseudo-table `sys_hub_flow_graph_diff`. The only currently allowed diff operations are `add_action` and `update_condition`. The validator rejects raw XML, raw `sys_update_xml`, unretrieved node references, scripts, custom actions, spokes, credentials, tokens, subflows, approvals, and broad graph rewrites. No runtime generation is enabled and `sys_hub_flow_graph_diff` is not accepted by retrieved Update Set handoff.

Flow graph diff unsupported-operation routing is based on structured Pydantic error locations, not string matching. When validation fails at the `requested_graph_diff` `operation` path, the validator raises the stable `unsupported Flow graph diff operation` diagnostic without stringifying the original `ValidationError`.

Flow graph diff operation diagnostics do not retain unsafe causes. Unsupported operations still fail with `unsupported Flow graph diff operation`, but the public `ValueError` does not chain the original Pydantic `ValidationError`. Crash reporters, traceback formatters, graph diff artifacts, and work-note writers therefore cannot re-expose operation payload fragments, validation metadata, unsupported operation values, or malformed exception text through `__cause__`.

Sprint 127 adds Flow Designer builder preflight planning. The preflight verifies `retrieved_graph_hash_matches_existing_graph_hash`, keeps `runtime_generation_enabled=false`, keeps retrieved Update Set handoff disabled, and reports `Flow Designer builder is design-only`; runtime generation remains disabled. Required evidence before implementation can proceed includes `xml_shape_repository_available`, customer update naming, flow snapshot update strategy, rollback customer update strategy, and ServiceNow preview/commit review.

Sprint 128 adds the Flow XML shape repository `flow-xml-shapes-v1`. The repository contains review metadata only for `sys_hub_flow`, `sys_hub_action_instance`, and `sys_hub_flow_logic_instance_v2` customer-update shapes. It records the `record_update` root, `INSERT_OR_UPDATE` action, required fields, forbidden fields, and shape-specific review notes. There is still no Flow XML builder and no retrieved Update Set handoff for Flow Designer.

Sprint 129 adds the Flow XML shape evidence validator `validate_flow_xml_shape_evidence`. Operators and future researchers can use it to validate retrieved review samples against `flow-xml-shapes-v1` before any builder work is considered. The validator rejects malformed XML, wrong root or action values, missing required field evidence, and forbidden field evidence. It adds `xml_shape_evidence_validator_available` to the preflight evidence list, but there is still no Flow XML builder and no retrieved Update Set handoff for Flow Designer.

Flow XML evidence collection record sets are exact containers before evidence validation or readiness evaluation. `collect_flow_xml_evidence()` requires `sys_hub_flow`, `sys_hub_action_instance`, `sys_hub_flow_logic_instance_v2`, `sys_update_xml`, and `sys_hub_flow_snapshot` fetch results to be exact lists containing exact dictionaries. List subclasses and record dictionary subclasses fail with `Flow XML evidence records contain non-JSON value` before flow matching, flow sys_id parsing, instance sys_id extraction, customer-update lookup, shape validation, snapshot hashing, metadata rendering, readiness evaluation, artifact persistence, or work-note generation can execute caller-controlled container hooks.

Flow XML shape evidence diagnostics do not retain unsafe causes. Malformed XML still fails with `Flow XML shape evidence is not valid XML`, but the public `ValueError` does not chain the lower-level XML parser exception. Crash reporters, traceback formatters, Flow evidence artifacts, and work-note writers therefore cannot re-expose XML parser fragments, line and column details, raw XML snippets, or malformed evidence through `__cause__`.

Sprint 130 adds the Flow customer update strategy `flow-customer-update-strategy-v1`. The strategy uses the existing ServiceNow-style `table_sys_id` update name convention for approved Flow tables, rejects unapproved Flow tables, rejects unstable non-hex sys_ids, and records rollback strategy coverage for `add_action` and `update_condition`. This gives the future builder a reviewable naming and rollback strategy, but there is still no Flow XML builder and no retrieved Update Set handoff for Flow Designer.

Sprint 131 adds the Flow snapshot update strategy `flow-snapshot-update-strategy-v1`. The strategy requires retrieved `latest_snapshot` evidence from `sys_hub_flow`, rejects missing or unstable snapshot references, and rejects snapshot/version table mutations because snapshot table mutation is not supported in the current Flow path. This keeps future Flow builder work anchored to retrieved instance evidence, but there is still no Flow XML builder and no retrieved Update Set handoff for Flow Designer.

Sprint 132 adds the Flow preview/commit review strategy `flow-preview-commit-review-strategy-v1`. The strategy names the human review boundary as `retrieved_update_set_preview_commit`, requires preview before commit, requires human commit, and rejects auto-commit because Flow Designer auto-commit is not supported. This keeps ServiceNow preview/commit as the review point, but there is still no Flow XML builder and no retrieved Update Set handoff for Flow Designer.

Sprint 133 adds the Flow builder readiness contract `flow-builder-readiness-v1`. The contract aggregates required Flow builder evidence into one auditable object, reports `missing_evidence`, and keeps both runtime generation and retrieved Update Set handoff disabled with the blocked reason `Flow Designer builder is not implemented`. This is still no Flow XML builder and no retrieved Update Set handoff for Flow Designer.

Sprint 134 adds Flow builder plan readiness wiring. Every Flow builder preflight plan now includes `readiness_contract_version`, `missing_builder_evidence`, `ready_for_runtime_generation=false`, `ready_for_retrieved_update_set_handoff=false`, and the readiness blocked reason. This keeps preflight consumers from treating a design-only plan as an implementation-ready builder. There is still no Flow XML builder and no retrieved Update Set handoff for Flow Designer.

Sprint 135 adds Flow unsupported reason codes. The readiness contract and every Flow builder preflight plan now include `unsupported_reason_codes` for routing and admin display. Current codes are `flow_builder_not_implemented`, `runtime_generation_disabled`, and `retrieved_update_set_handoff_disabled`. These codes do not enable mutation; there is still no Flow XML builder and no retrieved Update Set handoff for Flow Designer.

Sprint 136 adds Flow unsupported reason guidance. The readiness contract and every Flow builder preflight plan now include `unsupported_reason_guidance`, with stable summaries, the `route_to_human_review` operator action, and ServiceNow work note text. This gives operators actionable feedback without duplicating unsupported Flow prose in worker or admin code. There is still no Flow XML builder and no retrieved Update Set handoff for Flow Designer.

Sprint 137 adds the Flow preflight guidance artifact. When fulfillment sees `flow_modify`, the worker now stores a `flow_preflight_guidance` artifact with schema `flow-preflight-guidance-v1`, the `flow-builder-readiness-v1` disabled readiness flags, `unsupported_reason_codes`, and `unsupported_reason_guidance` including `route_to_human_review`. This makes Flow routing guidance visible in persisted runtime evidence while preserving the boundary: no Flow XML builder and no retrieved Update Set handoff for Flow Designer.

Sprint 138 adds the Flow preflight guidance work note. After artifacts are persisted, unsupported Flow stories still move to `u_ai_status=Human Review Required`, but the ServiceNow work note now includes `Flow preflight guidance artifact`, the `flow_preflight_guidance` artifact reference, and the `route_to_human_review` work-note guidance from the readiness contract. This makes the ServiceNow user surface actionable without creating a retrieved Update Set. There is still no Flow XML builder and no retrieved Update Set handoff for Flow Designer.

Flow round-trip verification report details are also stringification-safe. If the Retrieved Update Set import path raises a malformed exception while the harness records the `retrieved_update_set_imported` assertion, the report records `flow roundtrip raised unstringifiable <ExceptionType>` or `flow roundtrip raised unstringifiable exception` instead of letting a secondary exception break UAT evidence generation.

Flow graph round-trip state hashes are strict JSON. Each retrieved node's canonical representation is
serialized with strict JSON numeric handling before `flow_graph_state_hash()` computes the graph
digest. If corrupted node state contains `NaN`, `Infinity`, or `-Infinity`, hashing fails with
`Flow graph node canonical state contains non-finite numeric values`. The diagnostic does not echo
node field names or values, so UAT provenance cannot be minted over Python-only numeric tokens.

Flow graph hash diagnostics do not retain unsafe causes. Corrupted Flow graph node state still fails
with `Flow graph node canonical state contains non-finite numeric values`, but the public
`ValueError` does not chain the lower-level JSON encoder exception. Crash reporters, traceback
formatters, Flow evidence artifacts, and work-note writers therefore cannot re-expose node field
names, values, JSON token fragments, or malformed state through `__cause__`.

Flow XML shape evidence invalid reasons are stringification-safe as well. If shape validation raises a malformed exception while collecting `FlowXmlShapeEvidenceRecord.reason`, the evidence record stores `flow xml evidence raised unstringifiable <ExceptionType>` or `flow xml evidence raised unstringifiable exception` instead of breaking collection for the whole Flow evidence bundle.

Flow snapshot evidence hashes are strict JSON. Retrieved `sys_hub_flow_snapshot` rows are serialized
with strict JSON numeric handling before `content_sha256` is computed. If a snapshot row contains
non-finite numeric values such as `NaN`, `Infinity`, or `-Infinity`, the collector records
`sys_hub_flow_snapshot:invalid`, stores the stable reason
`flow_snapshot_evidence_invalid: non-finite snapshot value`, and does not preserve the malformed row
metadata in the evidence bundle. The reason does not echo snapshot field names, credential-like keys,
or values. Unsupported non-JSON row values are also rejected before hashing with
`flow_snapshot_evidence_invalid: non-JSON snapshot value`; snapshot evidence hashing does not call
`str()` or `repr()` on unsupported objects, bytes, or custom scalar values.

Flow graph diff safety scans are strict JSON too. The validators that scan model-proposed Flow
customer-update records for raw XML and graph diff payloads for forbidden tokens now serialize with
strict JSON numeric handling before scanning. If those candidate structures contain `NaN`,
`Infinity`, or `-Infinity`, validation fails before builder planning or handoff begins with a stable
non-finite diagnostic. The diagnostic does not echo the malformed field names or values.

Flow graph diff safety scans also reject non-JSON Python values before scanning. Unsupported scalar
objects, bytes, and other non-JSON values are not stringified through `str()` or `repr()` for token
or raw XML checks. Validation fails with a stable non-JSON diagnostic and does not echo malformed
field names, object type names, object string output, or values.

Flow graph diff payload diagnostics do not retain unsafe causes. Strict JSON validation for Flow graph diff payloads still fails with `Flow graph diff contains a non-finite payload value` or `Flow graph diff contains a non-JSON payload value`, but the public `ValueError` does not chain lower-level JSON encoder exceptions. Crash reporters, traceback formatters, Flow graph artifacts, and work-note writers therefore cannot re-expose payload keys, unsupported object type names, non-finite numeric tokens, or object string representations through `__cause__`.

Unsupported behavior includes graph rewrites, custom actions, spokes and integrations, credentials, secrets, tokens, API keys, subflows, approval orchestration, script steps, data migration, runtime execution history mutation, and direct mutation of Flow runtime state outside reviewed customer updates.

### Code Surface Analysis Capability

The `business_rule_analyze`, `client_script_analyze`, and `script_include_analyze` capabilities are context-only. They exist to inspect stories that appear to need ServiceNow code-surface work and retrieve the current platform records before any generation capability is approved.

Surface mappings:

- Business Rule analysis retrieves `sys_script`.
- Client Script analysis retrieves `sys_script_client`.
- Script Include analysis retrieves `sys_script_include`.

When selected, the runtime retrieves the required context, redacts script-like fields, stores an `instance_context_bundle`, and stores a `code-surface-analysis-v1` artifact. The analysis names the capability, surface, source table, target table or `global`, existing record count, unsupported cases, and context sufficiency. It does not call the model and does not create a retrieved Update Set.

The story receives human-review feedback through the normal work-note path. Code surface generation remains unsupported until separate mutation profiles define output schema, deterministic validators, retrieved Update Set XML evidence, and UAT expectations for each artifact type.

### CMDB IRE Analysis Capability and Candidate Capability

The `cmdb_ire_analyze` capability is context-only. The `cmdb_ire_generate` capability is candidate-generation only. Together they exist for stories that ask for CMDB Identification and Reconciliation Engine changes, such as using serial number as a primary identifier or match key across SCCM, Intune, Workspace ONE, Azure Arc, and ServiceNow device sources.

When selected, the runtime targets the relevant CMDB class, usually `cmdb_ci_computer` for device stories, and retrieves four required surfaces:

- `cmdb_ire_identification_rules` from `cmdb_identifier` and `cmdb_identifier_entry`.
- `cmdb_ire_reconciliation_rules` from `cmdb_reconciliation_definition`.
- `cmdb_data_sources` from `sys_object_source`.
- `cmdb_class_hierarchy` from `sys_db_object`.

The worker stores an `instance_context_bundle` and a `cmdb_ire_analysis` artifact with schema `cmdb-ire-analysis-v1`. CMDB IRE stories may now produce structured candidates for `cmdb_identifier`, `cmdb_identifier_entry`, and `cmdb_reconciliation_definition`, including reconciliation-rule intent, but retrieved Update Set handoff remains disabled because verified ServiceNow XML shape evidence is not yet captured for those tables.

CMDB IRE discovery record collections are exact containers before context dossier assembly. `cmdb_identifier`, `cmdb_identifier_entry`, and `sys_db_object` class hierarchy fetch results must be exact lists containing exact dictionaries. List subclasses and record dictionary subclasses fail with `discovery text metadata contains non-JSON value` before IRE rule iteration, active-state parsing, class filtering, citation counts, context dossier persistence, model invocation, ServiceNow import, or story writeback can execute caller-controlled container hooks.

CMDB IRE retrieved Update Set mutation is not enabled until identification-rule and reconciliation-rule validators, XML shape evidence, rollback strategy, and preview/commit evidence are approved.

### Business Rule Generation Capability

`business_rule_generate` is currently `candidate_generation` for the first production-hardening subset. The current maturity limit is `current_max_story_points=3`; the full maturity target remains `target_max_story_points=5`. Retrieved Update Set handoff remains disabled until executable-code XML evidence and validators are approved.

The supported subset is table-local Business Rules only: `before/after` timing, `insert/update` operations, one target table, one generated rule, and an explicit condition. Generated changes must become `sys_script` customer updates wrapped in `sys_update_xml` for retrieved Update Set review. Retrieved Update Set preview/commit remains the human review boundary.

Unsupported behavior includes delete rules, async/display rules, scheduled jobs, ACL changes, Script Include creation, no outbound REST or SOAP calls, no credentials or endpoint construction, no cross-table writes, no broad GlideRecord mutation, and no system-table mutation outside the intended `sys_script` customer update.

The provider output must be structured implementation intent, not authoritative XML. Required fields include target table, rule name, timing, operations, condition summary, condition expression, script body, fields read, fields written, test plan, rollback notes, and reviewer notes. Deterministic validators approve table context, operation scope, script safety, field access, secret detection, and parseable `sys_update_xml` before a retrieved Update Set can be imported. Scripts containing forbidden tokens such as `GlideRecord`, destructive update/delete APIs, outbound HTTP/S endpoints, credential access, passwords, tokens, or API keys fail closed before import.

### Client Script Generation Capability

The Sprint 117 Client Script Generation Profile Design is implemented for the first production-hardening subset. `client_script_generate` is currently `candidate_generation` with `current_max_story_points=3`; the full maturity target remains `target_max_story_points=5`. Retrieved Update Set handoff remains disabled until browser-side safety and XML evidence are approved.

The supported subset is table-local Client Scripts only: one generated `sys_script_client` record on one target table, `onLoad`, `onChange`, or `onSubmit` type, optional target field for `onChange`, and behavior implemented through ServiceNow client APIs such as `g_form`. Generated changes must become `sys_script_client` customer updates wrapped in `sys_update_xml` for retrieved Update Set review. Retrieved Update Set preview/commit remains the human review boundary.

Unsupported behavior includes DOM manipulation outside g_form APIs, `document` or `window` access, browser storage, `fetch` or `XMLHttpRequest`, endpoint construction, credentials, secrets, tokens, API keys, GlideAjax dependency creation, Script Include creation, ACL changes, integrations, cross-table writes, and system-table mutation outside the intended `sys_script_client` customer update.

The provider output must be structured implementation intent, not authoritative XML. Required fields include target table, script name, Client Script type, target field for `onChange`, condition summary, script body, fields read, fields written, messages shown, test plan, rollback notes, and reviewer notes. Deterministic validators approve table context, script type, target field, allowed client APIs, field access, secret detection, and parseable `sys_update_xml` before a retrieved Update Set can be imported. Any forbidden Client Script behavior fails closed before import.

### Script Include Generation Capability

The Sprint 119 Script Include Generation Profile Design is implemented for the first production-hardening subset. `script_include_generate` is currently `candidate_generation` with `current_max_story_points=3`; the full maturity target remains `target_max_story_points=5`. Retrieved Update Set handoff remains disabled until executable-code XML evidence and validators are approved.

The supported subset is server-side utility Script Includes only: one generated `sys_script_include` record per story, one named class or function, explicit scope, explicit client-callable decision, and no simultaneous caller creation. Generated changes must become `sys_script_include` customer updates wrapped in `sys_update_xml` for retrieved Update Set review.

Unsupported behavior includes global privilege escalation, cross-scope access changes, role changes, ACL changes, system property changes, credentials, secrets, tokens, API keys, outbound REST/SOAP/email/event calls, broad GlideRecord mutation, data migration, background repair logic, and any Script Include that requires simultaneous Business Rule, Client Script, Flow, scheduled job, or integration creation.

client callable Script Includes are not supported in the first implementation because that would also require GlideAjax caller design. The provider output must be structured implementation intent, not authoritative XML. Required fields include Script Include name, API name, scope, client-callable flag, active flag, description, script body, public methods, tables read, tables written, fields read, fields written, test plan, rollback notes, and reviewer notes. Deterministic validators approve identifier shape, retrieved Script Include context, script safety, caller boundary, secret detection, and parseable `sys_update_xml` before a retrieved Update Set can be imported. Any forbidden Script Include behavior fails closed before import.

### UI Policy Generation Capability

The Sprint 122 UI Policy Generation Profile Design is implemented for the first production-hardening subset. `ui_policy_generate` is enabled with `current_max_story_points=3`; the full maturity target remains `target_max_story_points=5`. In this registry, `enabled` means the deterministic builder can create retrieved Update Set handoff artifacts now.

The supported subset is declarative, table-local UI Policy behavior only: one generated `sys_ui_policy` record and one or more generated `sys_ui_policy_action` records, an explicit target table, an explicit condition, an explicit reverse-if-false decision, and field actions limited to mandatory, visible, or read-only behavior. Generated changes become `sys_ui_policy` and `sys_ui_policy_action` customer updates wrapped in `sys_update_xml` for retrieved Update Set review.

Unsupported behavior includes run scripts, advanced scripts, Client Script behavior, `g_form` logic, Business Rule creation, Script Include creation, Flow creation, ACL changes, integration calls, cross-table behavior, data migration, role changes, system property changes, credentials, secrets, tokens, and API keys.

The provider output must be structured implementation intent, not authoritative XML. Required fields include target table, policy name, condition, reverse-if-false decision, run-scripts flag, view, fields read, UI Policy actions, test plan, rollback notes, and reviewer notes. Deterministic validators approve table context, form layout context, existing UI Policy context, condition fields, action fields, run-scripts disabled state, forbidden token checks, and parseable `sys_update_xml` before a retrieved Update Set can be imported. Any forbidden UI Policy behavior fails closed before import.

## CI/CD Update Set API Capability

Use `check-cicd-update-set-capability` to verify that the target ServiceNow instance exposes the Yokohama+ CI/CD Update Set API before designing promotion around it:

```bash
python3 -m jedi_devproject.cli check-cicd-update-set-capability --env-file .env
```

The command is read-only. It sends non-mutating `POST /api/sn_cicd/update_set/create` and `POST /api/sn_cicd/update_set/retrieve` probes without the required parameters. A `400` response naming `update_set_name` or `update_set_id` is treated as evidence that the API route is installed and reachable by the OAuth identity. `401`, `403`, and `404` fail closed.

Malformed successful CI/CD probe responses also fail closed. If ServiceNow returns a present `result` value that is not an object, the capability probe records `malformed_result_payload` and does not echo the malformed `result` value into CLI output, artifacts, logs, or ServiceNow work notes.

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

Update Set importer bootstrap lookup handling is strict. `apply_update_set_importer_records()` and `verify_update_set_importer_records()` accept only primitive string, boolean, and integer scalar values for returned `sys_ws_definition.sys_id` values before creating or verifying the `sys_ws_operation` record. Unsupported ServiceNow response values fail with `Update Set importer lookup contains non-JSON value`; the bootstrap path does not call `str()` or `repr()` on unsupported ServiceNow response values.

Update Set importer bootstrap verification records require exact dictionaries. `verify_update_set_importer_records()` accepts only `None` or exact Python dictionaries from `fetch_table_record()` before comparing `sys_ws_definition` or `sys_ws_operation` fields. Dict subclasses, mapping-like records, and unsupported record containers fail with `Update Set importer lookup contains non-JSON value` before field mismatch checks, `sys_id` extraction, dependent operation lookups, verification-result recording, or fetched-record hooks can run.

Update Set importer bootstrap apply results are strict too. `apply_update_set_importer_records()` accepts only exact Python dictionaries from each `sys_ws_definition` and `sys_ws_operation` upsert, then validates the returned `sys_id` before adding it to `upserted_records`. Dict subclasses and unsupported response values fail with `Update Set importer lookup contains non-JSON value` before response-field access, dependent operation upserts, apply-result recording, or before an apply result can expose object representations, bytes, containers, and credential-like response fragments.

Update Set importer lookup text values require exact strings. String subclasses returned from `sys_ws_definition.sys_id` or `sys_ws_operation.sys_id` upsert and verification lookups fail with `Update Set importer lookup contains non-JSON value` before dependent operation upserts, operation verification lookups, apply results, or verification results can reuse the corrupted identifier.

The PDI importer smoke on May 14, 2026 posted a minimal reviewed XML payload to the discovered endpoint `/api/1860704/jedi_update_set_import`. ServiceNow returned `201` with `status=imported` and created retrieved update set `JEDI XML Import Smoke 20260514 002` with sys_id `64c3e9d1b27a42479620114da017857a`, state `loaded`, and zero `sys_update_xml` rows. This proves the server-side XML import bridge works for retrieved update set headers; the next smoke must include real customer update rows.

The follow-on PDI smoke posted XML containing one `sys_remote_update_set` header plus two `sys_update_xml` customer update rows for a disposable field `u_jedi_import_smoke_notes`. ServiceNow created retrieved update set `JEDI XML Import Customer Updates Smoke 20260514 001` with sys_id `22221e3514c94fa3bde48148b0053e6f`, state `loaded`, and two remote customer updates: `sys_dictionary_rm_story_u_jedi_import_smoke_notes` and `sys_documentation_rm_story_u_jedi_import_smoke_notes_en`. Both rows were linked through `remote_update_set`; neither had a local `update_set`.

The CI/CD preview smoke for that retrieved update set succeeded. `preview_cicd_update_set()` returned progress id `d240c02ec330c710913fbf12b4013170`; progress completed with `status_label=Successful`, `percent_complete=100`, `has_preview_problem=false`, and `remote_update_set_id=22221e3514c94fa3bde48148b0053e6f`. The retrieved update set state became `previewed`, and `sys_update_preview_problem` returned zero rows. No commit was run.

## Container Runtime

The local container runtime is defined by `Dockerfile` and `docker-compose.yml`. It starts three services:

- `postgres`: PostgreSQL operational state.
- `api`: FastAPI lifecycle receiver.
- `worker`: one-shot fulfillment worker process.

The hosted API image binds to `${PORT:-8000}`. This keeps local container runs on port 8000 while
honoring platform-assigned ports from Railway or another container host. The container healthcheck calls `GET /health` on the same bound port with a 20 second start period, 30 second interval, 5 second timeout, and 3 retries. The healthcheck is a liveness probe only; use `/ready` when the deployment needs PostgreSQL readiness.

Container images run as `jedi`, not root. Both `Dockerfile` and `Dockerfile.worker` create a system
user and group, prepare `/app/artifacts`, set ownership to `jedi:jedi`, and switch to `USER jedi`
before the API or worker command starts. This keeps filesystem write access scoped to the application
directory and prevents the hosted runtime process from running with root privileges.

Compose reduces API and worker container privileges with `security_opt: no-new-privileges:true` and
`cap_drop: [ALL]`. This hardens the app processes beyond the non-root image user by preventing
privilege escalation and dropping ambient Linux capabilities during local runtime verification.

Compose app containers use read-only root filesystems. The `api` and `worker` services set
`read_only: true`, mount `/tmp` as tmpfs for bounded temporary-file compatibility, and keep
`/app/artifacts` as the explicit writable named volume for audit output and legacy runtime artifacts.

Container images default `JEDI_AUDIT_ROOT` to `/app/artifacts/audit`. Both runtime images create
that directory before switching to `USER jedi`, so local audit artifacts and legacy smoke outputs
write to an owned application path unless the deployment explicitly overrides the setting.

Compose API readiness healthcheck calls `GET /ready` from inside the `api` container. This makes
`docker compose ps` show whether the runtime API can reach the PostgreSQL operational store during
local hardening runs, while the image-level Dockerfile healthcheck remains a cheap `/health`
liveness probe.

Compose worker startup waits for API readiness as well as Postgres readiness. The worker service
depends on `postgres` and `api` with `condition: service_healthy`, so local orchestration does not
start fulfillment before the API has proven operational-store reachability through `/ready`.

Compose service logs are bounded. The `postgres`, `api`, and `worker` services use the Docker
`json-file` logging driver with `max-size: "10m"` and `max-file: "5"` so repeated local hardening,
UAT, or lifecycle replay runs cannot grow container logs without an explicit operator decision.

Compose app services use Docker's init shim. The `api` and `worker` services set `init: true` so
local runtime containers get PID 1 signal forwarding and child-process reaping without embedding
that process-management concern into the application entrypoints.

Compose app services limit process counts. The `api` and `worker` services set `pids_limit: 256`
to contain process-count exhaustion during local lifecycle replay, test, or worker fault scenarios
without tuning the Postgres container in the same application-runtime hardening slice.

Compose app services define graceful shutdown windows. The `api` and `worker` services use
`stop_signal: SIGTERM` with `stop_grace_period: 30s`, making local stop behavior explicit and giving
runtime loops a bounded interval to finish cleanup before Docker escalates termination.

Compose binds the local API port to loopback only. The `api` service publishes
`127.0.0.1:8000:8000` instead of broad `8000:8000`, so local webhook and admin-console testing do
not expose the runtime API on every host interface unless an operator deliberately changes the
compose file.

Run the local stack with:

```bash
docker compose up --build
```

Compose requires split ServiceNow PM/DEV values in the host environment:
`SERVICENOW_PM_INSTANCE_URL`, `SERVICENOW_PM_CLIENT_ID`, `SERVICENOW_PM_CLIENT_SECRET`,
`SERVICENOW_DEV_INSTANCE_URL`, `SERVICENOW_DEV_CLIENT_ID`, and `SERVICENOW_DEV_CLIENT_SECRET`.
`SERVICENOW_INSTANCE_URL` remains a direct-runtime fallback with `SERVICENOW_CLIENT_ID` and
`SERVICENOW_CLIENT_SECRET` for non-compose local compatibility only. Compose sets `DATABASE_URL`
to the local `postgres` service and writes audit output under `/app/artifacts/audit`.

Local compose requires `JEDI_POSTGRES_PASSWORD`. The value is used for both `POSTGRES_PASSWORD` and `DATABASE_URL`; do not hardcode the database password in `docker-compose.yml`. Compose fails before service creation when the variable is missing, which keeps local smoke runs from normalizing a shared default database credential.
The example env file includes `JEDI_POSTGRES_PASSWORD=` as an empty required placeholder. Operators
must set a local value before running `docker compose up --build`; the sample intentionally does not
ship a shared default.

Local compose restart policies are explicit. `postgres` uses `restart: unless-stopped` so the
operational store is durable across routine local container restarts. `api` and `worker` use
`restart: on-failure`, which restarts crashed runtime processes during smoke and operator testing
without fighting intentional `docker compose stop` or clean process exits.

Compose uses role-specific images. `api` builds from `Dockerfile`, which sets
`JEDI_RUNTIME_ROLE=api`, and `worker` builds from `Dockerfile.worker`, which sets
`JEDI_RUNTIME_ROLE=worker`. Do not run the worker command from the API image in compose; that hides
role-boundary mistakes during local smoke tests.

Compose also declares service-level runtime roles. `api` sets `JEDI_RUNTIME_ROLE=api`, and `worker`
sets `JEDI_RUNTIME_ROLE=worker` in service environment configuration. This duplicates the image
default intentionally so local orchestration still enforces role boundaries if a Dockerfile default
or compose command changes later.

`JEDI_BUILD_CLAIM_APPLY` defaults to `false` in compose. Keep it false for local runtime verification until the story, webhook, and writeback behavior have been reviewed for the target PDI.

For hosted runtime, the worker process should run `python -m jedi_devproject.runtime_worker` from `Dockerfile.worker`. The worker loop is controlled by:

- `JEDI_WORKER_MAX_ITERATIONS`: optional bounded loop count for smoke tests and batch workers.
- `JEDI_WORKER_IDLE_SLEEP_SECONDS`: idle poll sleep interval. Defaults to `5.0`.
- `JEDI_WORKER_STOP_ON_FAILURE`: whether the process exits after the first failed job. Defaults to `false` for long-running workers.

`JEDI_WORKER_MAX_ITERATIONS` is optional. Leaving it unset creates an unbounded long-running
worker. When set, it must be greater than zero so a smoke or batch worker cannot silently start and
exit without processing. `JEDI_WORKER_MAX_ITERATIONS<=10000`; unset remains the deliberate long-running worker mode.

`JEDI_WORKER_STOP_ON_FAILURE=false` in production is required so a single failed fulfillment job cannot intentionally stop the hosted worker. Use stop-on-failure only for local smoke tests or bounded development runs where the operator is watching the process.

`JEDI_WORKER_IDLE_SLEEP_SECONDS=0` is valid only for bounded smoke runs that set
`JEDI_WORKER_MAX_ITERATIONS`. Unbounded workers must use a positive idle sleep interval so an idle
queue cannot create a tight polling loop. `JEDI_WORKER_IDLE_SLEEP_SECONDS<=300`, so workers cannot appear healthy while sleeping or delaying maintenance for days.

`run_loop()` rejects invalid direct worker controls before processing starts. Embedded callers cannot bypass worker settings loading with non-positive or oversized `JEDI_WORKER_MAX_ITERATIONS`, unbounded zero `JEDI_WORKER_IDLE_SLEEP_SECONDS`, non-finite or oversized sleep values, non-positive or oversized maintenance intervals, or `JEDI_WORKER_STOP_ON_FAILURE=true` in production. Invalid direct controls fail before the processor, pruner, stale-job recoverer, alert emitter, or sleep function runs.

Embedded worker runtime mode checks use the same exact-string boundary as startup validation. `run_once()` validates `RuntimeSettings.runtime_role` before checking for the API-only role, and `run_loop()` validates `RuntimeSettings.runtime_environment` before enforcing production `JEDI_WORKER_STOP_ON_FAILURE=false`. Malformed direct runtime role or environment objects fail with the setting-name runtime diagnostic before worker role branching, production stop-on-failure checks, processor calls, maintenance calls, alert emitters, store work, or sleep calls.

Worker boolean environment values are strict. `JEDI_WORKER_STOP_ON_FAILURE` and
`JEDI_STALE_JOB_REQUEUE_ENABLED` accept only `true`, `false`, `1`, `0`, `yes`, `no`, `on`, or
`off`, case-insensitively and without padding or control characters. Malformed values fail worker settings loading instead of being silently treated as false; diagnostics include the setting name and do not silently normalize operator input.

Worker numeric environment values are strict. `JEDI_WORKER_MAX_ITERATIONS` and
`JEDI_STALE_JOB_REQUEUE_BATCH_SIZE` must parse as ASCII base-10 digits only without signs, underscores, padding, or control characters. `JEDI_WORKER_IDLE_SLEEP_SECONDS`, `JEDI_RETENTION_PRUNE_INTERVAL_SECONDS`,
and `JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS` must parse as finite numbers without padding or
control characters, and the accepted token format is now fixed ASCII decimal numbers without signs, underscores, or exponent notation; non-finite values such as `nan`, `inf`, and `-inf` are rejected. Malformed values fail worker settings loading with the setting name instead of surfacing raw parser errors or silently normalizing operator input. Worker decimal parser error wrapping also uses the shared safe exception diagnostic helper, so malformed parser exception objects fail as `runtime worker raised unstringifiable <ExceptionType>` or `runtime worker raised unstringifiable exception` instead of letting secondary stringification errors leak configuration-adjacent text.

Railway development now uses `JEDI_BUILD_CLAIM_APPLY=true` so live fulfillment moves the story to `Work in Progress` before model candidate generation. Keep the worker as a separate service from the public API service.

## Hosted Railway Process Split

`railway.json` is the API service manifest. It builds from `Dockerfile`, lets the container command
bind to `${PORT:-8000}`, exposes `/ready` as the Railway healthcheck path, and uses an on-failure
restart policy. Railway deploy healthcheck uses `/ready` so hosted rollout checks include
PostgreSQL operational-store reachability. The container liveness probe still uses `/health` inside
the image because it only verifies that the API process can answer HTTP. The API service owns
`/health`, `/ready`, lifecycle webhooks, and the admin console.

`deploy/railway/worker-service.json` is the worker service template. Use it when creating the
separate hosted worker service from the same repository. The worker builds from `Dockerfile.worker`
and starts with `python -m jedi_devproject.runtime_worker`. The worker service must not expose a public HTTP process, must not define a public healthcheck path, and should share the same PostgreSQL-backed operational store as the API service.

Both hosted services need the same runtime configuration boundary for database access, ServiceNow
PM/DEV credentials, model provider credentials, and audit paths. API-only secrets such as lifecycle
webhook HMAC validation belong on the API service. Worker-only secrets such as model provider API
keys belong on the worker service unless a deployment owner intentionally centralizes environment
management at the project level.

## Runtime Role Boundary

`JEDI_RUNTIME_ROLE=api` is the public API role. The API image sets this role by default. In
production validation, the API role owns lifecycle webhook authentication, admin authentication,
`/health`, `/ready`, and the admin console. Worker-only settings such as `JEDI_MODEL_PROVIDER`,
`OPENAI_API_KEY`, `OPENAI_MODEL`, `JEDI_PUBLIC_WEB_ACCESS=worker`, and
`JEDI_BUILD_CLAIM_APPLY=true` or `JEDI_UPDATE_SET_APPLY=true` are rejected when the API role is
active. The runtime API factory also rejects `JEDI_RUNTIME_ROLE=worker` before opening the
operational store, so a worker-configured environment cannot accidentally expose lifecycle or admin
HTTP routes.

`JEDI_RUNTIME_ROLE=worker` is the private fulfillment worker role. The worker image sets this role by
default. In production validation, the worker role owns model execution, public documentation
retrieval when enabled, Update Set handoff behavior, stale-job recovery, retention pruning, and
failure alert emission. API-only settings such as `JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE`,
`JEDI_LIFECYCLE_WEBHOOK_SECRET`, `JEDI_ADMIN_API_TOKEN`, `JEDI_ADMIN_AUTH_MODE`, and local admin
console credentials are rejected when the worker role is active. Worker entrypoints also reject
`JEDI_RUNTIME_ROLE=api` before invoking the fulfillment processor, so an API-configured environment
cannot accidentally claim or fulfill queued work. The direct fulfillment processor also rejects
`JEDI_RUNTIME_ROLE=api` before creating ServiceNow clients, opening the operational store, or
claiming queued work; external schedulers must use the worker role for fulfillment execution.

`JEDI_RUNTIME_ROLE=combined` remains the default for local development and legacy tests. Hosted production validation rejects the combined role unless `JEDI_ALLOW_COMBINED_PRODUCTION=true` is set as an explicit deployment-owner acceptance that a single process owns both public API and private worker responsibilities. Split production roles reject `JEDI_ALLOW_COMBINED_PRODUCTION=true`; keep exception flags off `api` and `worker` services so config audits stay unambiguous.

`JEDI_TRUSTED_HOSTS` is also API-only. Production worker services reject it because workers do not serve public HTTP requests and should not carry public Host header policy. Keep trusted-host allowlists on `api` or intentionally combined services only.

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

Lifecycle webhook bootstrap lookup handling is strict. `apply_lifecycle_webhook_records()` and `verify_lifecycle_webhook_records()` accept only primitive string, boolean, and integer scalar values for returned `sys_rest_message.sys_id` values before creating or verifying the `sys_rest_message_fn` record. Unsupported ServiceNow response values fail with `Lifecycle webhook lookup contains non-JSON value`; the bootstrap path does not call `str()` or `repr()` on unsupported ServiceNow response values.

Lifecycle webhook bootstrap verification records require exact dictionaries. `verify_lifecycle_webhook_records()` accepts only `None` or exact Python dictionaries from `fetch_table_record()` before comparing `sys_rest_message`, `sys_rest_message_fn`, or `sys_script` fields. Dict subclasses, mapping-like records, and unsupported record containers fail with `Lifecycle webhook lookup contains non-JSON value` before field mismatch checks, `sys_id` extraction, dependent REST method lookups, verification-result recording, or fetched-record hooks can run.

Lifecycle webhook bootstrap apply results are strict too. `apply_lifecycle_webhook_records()` accepts only exact Python dictionaries from each `sys_rest_message`, `sys_rest_message_fn`, and `sys_script` upsert, then validates the returned `sys_id` before adding the record to `upserted_records`. Dict subclasses and unsupported response values fail with `Lifecycle webhook lookup contains non-JSON value` before response-field access, dependent REST method upserts, apply-result recording, or before an apply result can expose object representations, bytes, containers, and credential-like response fragments.

Lifecycle webhook lookup text values require exact strings. String subclasses returned from `sys_rest_message.sys_id`, `sys_rest_message_fn.sys_id`, or `sys_script.sys_id` upsert and verification lookups fail with `Lifecycle webhook lookup contains non-JSON value` before dependent method upserts, method verification lookups, apply results, or verification results can reuse the corrupted identifier.

Lifecycle webhook verification metadata normalization is safe. `verify_lifecycle_webhook_records()` normalizes only exact strings, exact booleans, exact integers, nulls, and safe ServiceNow reference dictionaries before comparing actual records to the bootstrap plan. String subclasses and unsupported metadata values collapse to a fixed non-matching sentinel before boolean normalization, reference comparison, mismatch collection, or result reporting can execute caller-controlled string or comparison methods.

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

Legacy external-build structured writeback fields are diagnostic surfaces too. Before
`plan_external_build_writeback()` returns values for `u_ai_build_reference` or
`u_ai_candidate_artifact`, it redacts credential-like fragments, collapses whitespace/control
characters, and bounds each value to 500 characters. This keeps legacy Table API writes from
storing raw build-system secrets, unsafe URLs, or multiline payload fragments in visible ServiceNow fields
while preserving the retrieved Update Set handoff path's dedicated metadata fields.
The build-claim path uses the same structured-field sanitizer before
`plan_story_build_claim_writeback()` returns an optional `u_ai_candidate_artifact` value, so a claim
note cannot preserve a raw candidate artifact URL or credential-like fragment in a visible
ServiceNow field.

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

Writeback state-choice mapping is exact-string only. `build_state_mapping_from_choices()` reads
ServiceNow state choice labels and values only when they are exact strings; string subclasses,
objects, numbers, and other malformed choice values are skipped without coercion. If `Ready for
Testing` cannot be found with a non-empty exact string value, the mapper returns no state mapping and
the writeback planner fails closed instead of guessing or executing custom string conversion hooks.

Writeback orchestration state-choice lookup is exact-shape guarded before state mapping. `evaluate_writeback_capability()`, `verify_writeback()`, and `execute_writeback()` accept only an exact Python list containing exact `StoryStateChoice` records from `fetch_story_state_choices()`. List subclasses, alternate iterables, model subclasses, and malformed entries fail with `writeback state choices contain non-JSON value` before iteration hooks, `model_dump()` hooks, Ready-for-Testing mapping construction, capability decisions, verification comparison, story mutation, audit writing, or writeback report construction can execute caller-controlled behavior.

Writeback orchestration dictionary-field lookup is exact-shape guarded before required-field validation. `evaluate_writeback_capability()`, `execute_writeback()`, and `execute_build_claim()` accept only exact Python lists containing exact `StoryDictionaryField` records from `fetch_story_dictionary_fields()`. List subclasses, alternate iterables, model subclasses, and malformed entries fail with `writeback dictionary fields contain non-JSON value` before iteration hooks, model hooks, dictionary field extraction, capability decisions, writeback plan validation, story mutation, audit writing, or writeback report construction can execute caller-controlled behavior.

Writeback orchestration story lookup is exact-shape guarded before story-not-found handling, indexing, or model operations. `verify_writeback()`, `execute_writeback()`, and `execute_build_claim()` accept only exact Python lists containing exact `Story` records from `fetch_stories()`. List subclasses, alternate iterables, model subclasses, and malformed entries fail with `writeback stories contain non-JSON value` before truthiness hooks, indexing hooks, `model_copy()` hooks, verification comparison, state checks, writeback planning, story mutation, audit writing, or writeback report construction can execute caller-controlled behavior.

Use `verify-writeback` after apply to read the remote story and confirm the structured writeback fields match the expected build result:

```bash
python3 -m jedi_devproject.cli verify-writeback \
  --env-file .env \
  --story-number STRY0010013 \
  --build-reference build-20260513-001 \
  --artifact-url artifacts/STRY0010013.json
```

The command is read-only. It discovers the instance `Ready for Testing` state value, fetches the story, and compares `state`, `u_ai_status`, `u_ai_build_reference`, and `u_ai_candidate_artifact`. It prints `verified=True` only when all expected fields match. Verification normalizes expected legacy structured fields through the same sanitizer as writeback planning before comparison, so a successful sanitized writeback is not reported as a mismatch just because the operator supplied the original build-system reference or artifact URL. Verification still compares against the raw remote ServiceNow values internally, but returned `actual_fields` are sanitized diagnostics: credential-like fragments are redacted, whitespace/control characters are collapsed, and values are bounded before CLI or report rendering.

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

Local artifact filenames and single-directory path components are validated before write-once artifact creation. Shared artifact writers reject empty names, `.` or `..`, absolute paths, path separators, and control characters before joining a filename to the artifact root. This covers generic JSON artifacts, lifecycle manifests, delivery attachment audits, reviewed delivery manifests, candidate run directories, candidate filenames, writeback audit filenames, and build-claim audit filenames, so operator-controlled run ids, story numbers, and derived artifact names cannot escape the configured artifact root.

Local write-once artifact creation uses exclusive file creation instead of a separate exists-then-write check. Existing files, existing symlinks, and broken symlinks are rejected before content is written, which prevents artifact overwrites, race-window replacement, and symlink redirection outside the artifact root.

Local artifact SHA-256 provenance hashing requires a regular file at the provided path. Symlinked artifact paths and non-regular filesystem entries are rejected before hashing, so lifecycle manifests, handoff reports, reviewed delivery jobs, and attachment verification do not treat filesystem indirection as authoritative artifact evidence. Missing artifact paths still fail closed through the existing missing-file behavior.

Artifact filesystem diagnostics do not retain unsafe causes. Write-once artifact collisions still fail with `artifact already exists:`, and symlinked or non-regular artifact reads still fail with `artifact path must be a regular file`, but public `ArtifactWriteError` and `ArtifactReadError` values do not chain lower-level filesystem exceptions. Logs, artifact manifests, work notes, admin diagnostics, and crash reporters therefore cannot re-expose local filesystem exception details, path fragments, or platform-specific errno text through `__cause__`.

Artifact manifest path serialization is strict at the local writer boundary. Lifecycle manifests, reviewed delivery lifecycle manifests, and delivery attachment audits accept only concrete platform `pathlib.Path` values when persisting artifact path strings. Path subclasses and other path-like objects fail with `artifact path must be a concrete pathlib Path` before manifest JSON is written or artifact hashes are calculated. This prevents corrupted in-process path objects from executing custom string conversion while audit manifests are being created.

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

Reviewed Update Set XML validation is bounded. The handoff job scans reviewed XML artifacts in chunks to reject leading `placeholder_update_set` exports and require a `sys_update_xml` customer update marker without calling `Path.read_text()` or loading the entire XML payload into memory. If the required marker is not found inside the bounded scan window, the artifact fails closed with `reason=reviewed_export_artifact_required`.

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
The artifact handoff work note sanitizes the report path and summary values before delivery:
values are redacted, whitespace/control characters are collapsed, and each value is capped at
500 characters including the truncation marker.

Artifact handoff CLI story lookup results are exact-shape guarded before ServiceNow mutation. `write-artifact-handoff-summary` and `attach-delivery-artifacts` accept only exact Python lists containing exact `Story` records from `fetch_stories()`. List subclasses, alternate iterables, model subclasses, and malformed entries fail with `story_lookup_result_unsafe` before truthiness hooks, indexing hooks, work-note update, attachment upload, attachment audit writing, or story sys_id exposure can execute caller-controlled behavior.

Pipeline and implementation CLI story lookup results are exact-shape guarded before candidate generation. `run-pdi`, `build-implementation-packet`, `build-implementation-candidate`, and `run-lifecycle-smoke` accept only exact Python lists containing exact `Story` records from ServiceNow story fetches. List subclasses, alternate iterables, model subclasses, and malformed entries fail with `story_lookup_result_unsafe` before truthiness hooks, indexing hooks, pipeline execution, packet generation, candidate artifact writing, lifecycle manifest writing, or dry-run writeback planning can execute caller-controlled behavior.

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

Attachment audit values are exact-string only. Delivery-job artifact fields are read from the
validated handoff report only when they remain exact strings, and malformed values fail with
`artifact_handoff_report_invalid` before audit writing. The ServiceNow Attachment API response
`sys_id` is external response metadata; if it is missing, empty, non-string, string-subclass, or
unstringifiable, the audit records `[attachment sys_id unavailable]` instead of coercing it with
`str()` or dropping the rest of the post-upload audit evidence.

Before apply calls ServiceNow, `attach-delivery-artifacts` recalculates each delivery file hash and compares it to the handoff report `artifact_sha256`. A missing file fails closed with `reason=artifact_missing`; a changed file fails closed with `reason=artifact_hash_mismatch`; no attachment is uploaded in either case. Dry-run attachment planning also verifies the same hashes before reporting planned attachments. The attachment audit records the reviewed `artifact_sha256` for each uploaded file.

Artifact handoff report story numbers are exact-string only at the CLI boundary. Both
`write-artifact-handoff-summary` and `attach-delivery-artifacts` reject missing, empty, numeric, or
otherwise malformed `story_number` values with `reason=artifact_handoff_report_invalid` before
printing story-specific summaries, checking confirmation values, building ServiceNow queries,
creating clients, or attaching files. The commands do not coerce malformed report identifiers with
`str()`.

Delivery handoff SHA-256 values are calculated with streaming file reads. Artifact SHA-256 values are calculated with streaming file reads across lifecycle manifest artifact references, intake feedback artifact references, handoff report generation, reviewed delivery artifact job creation, and delivery attachment hash verification. These paths all use the shared artifact hash helper to hash artifacts in bounded chunks instead of loading the entire artifact into memory.

Reviewed Update Set XML marker validation uses the same regular-file artifact reader before accepting a reviewed delivery job. Placeholder detection and `sys_update_xml` marker scanning reject symlinked paths and non-regular filesystem entries before reading XML bytes, so review eligibility checks cannot bypass artifact provenance file safety controls.

External-build result processing uses a typed `SuccessfulBuildRequiredError` when a failed or blocked build has no reviewed delivery artifacts. The CLI catches that type directly and writes only the Ready-for-Testing/writeback job for failed builds; it does not compare exception message text to decide whether delivery jobs should be skipped.

ServiceNow story attachment uploads are bounded before file contents are read. The ServiceNow client rejects attachment files larger than 10 MiB before OAuth token acquisition or Attachment API upload, so a local delivery artifact cannot create unbounded memory pressure during attachment handoff. Attachment upload uses the same regular-file artifact reader as provenance hashing: symlinked paths and non-regular filesystem entries are rejected before upload, and normal attachments are streamed in bounded chunks instead of using whole-file `read_bytes()`. Attachment upload error classification uses typed artifact read reasons from `ArtifactReadError.reason`, so oversized-file and regular-file diagnostics do not depend on exception message prefixes. Symlinked or non-regular attachment paths fail with the fixed diagnostic `ServiceNow attachment file must be a regular file` without echoing local path values, filenames, URL fragments, or credential-like payloads.

ServiceNow attachment read diagnostics do not retain unsafe causes. Oversized attachment artifacts fail with `ServiceNow attachment file exceeds 10485760 bytes`, while symlinked, missing, spoofed, or non-regular attachment artifacts fail with `ServiceNow attachment file must be a regular file`. Those public `ServiceNowApiError` instances suppress the original `ArtifactReadError`, so crash reporters, traceback formatters, and work-note writers do not retain local file paths, path-derived credential fragments, spoofed artifact read messages, or oversized-file implementation details in `__cause__`.

Attachment target story ids are validated before local file reads. `ServiceNowClient.attach_story_file()` applies the ServiceNow record-id path safety rule to `story_sys_id` before reading the attachment artifact, acquiring an OAuth token, or constructing the Attachment API request. Unsafe attachment target ids fail with `ServiceNow API record id is unsafe`; the diagnostic does not echo record id values, URL fragments, or credential-like payloads.

Attachment upload metadata is validated before local file reads as well. `ServiceNowClient.attach_story_file()` rejects unsafe attachment `file_name` and `content_type` values before reading the attachment artifact, acquiring an OAuth token, or constructing the Attachment API request. Attachment file names may contain ordinary internal spaces but must be strings, non-empty, unpadded, no longer than 255 characters, and free of path separators and control characters. Attachment content types must be string, no longer than 255 characters, and simple MIME type/subtype tokens such as `application/xml`; header parameters, whitespace, and control characters are rejected. Non-string and unsafe metadata fails with fixed diagnostics, `ServiceNow attachment file name is unsafe` or `ServiceNow attachment content type is unsafe`, before string-method calls and without echoing object type names, object string output, submitted metadata values, URL fragments, header-injection text, or credential-like payloads; oversized metadata uses the same fixed diagnostics. The diagnostics also fail without echoing submitted metadata values.

ServiceNow attachment file-name validation is type-safe before string handling and before local file reads. Attachment file names must be exact `str` instances. Non-string values and string subclasses fail with `ServiceNow attachment file name is unsafe` before trim checks, special-name checks, length checks, path-separator checks, whitespace/control-character scans, local artifact reads, OAuth token acquisition, Attachment API request construction, or transport calls; the diagnostic does not echo object type names, object string output, submitted file-name values, URL fragments, or credential-like payloads.

ServiceNow attachment content-type validation is type-safe before string handling and before local file reads. Attachment content types must be exact `str` instances. Non-string values and string subclasses fail with `ServiceNow attachment content type is unsafe` before trim checks, length checks, MIME token pattern matching, local artifact reads, OAuth token acquisition, Attachment API request construction, header construction, or transport calls; the diagnostic does not echo object type names, object string output, submitted content-type values, header-injection text, URL fragments, or credential-like payloads.

CLI JSON input files are bounded before parsing. Operator-supplied provider responses, implementation candidate jobs, handoff reports, handoff job files, sample stories, and writeback job files are read through a shared JSON loader that rejects inputs larger than 10 MiB with `json_input_too_large` before JSON parsing. The same loader requires a regular file and rejects symlinked or non-regular JSON input paths with `json_input_must_be_regular_file`, so local orchestration cannot silently follow filesystem indirection for provider responses, lifecycle specs, handoff reports, or job files. Invalid UTF-8 bytes fail as `json_input_invalid_utf8`. JSON input loader size, regular-file, and decode diagnostics preserve the reason code and configured byte limit without echoing the raw input path or payload fragments.

CLI JSON input diagnostics do not retain unsafe causes. Symlinked or non-regular JSON input paths still fail with `json_input_must_be_regular_file`, invalid UTF-8 still fails with `json_input_invalid_utf8`, and malformed or non-finite JSON still fails with `json_input_invalid_json`, but those public `ValueError` instances do not chain the underlying `ArtifactReadError`, `UnicodeDecodeError`, `JSONDecodeError`, or parser `ValueError`. This keeps traceback, API, and CI error serialization from re-exposing sensitive local paths, raw bytes, decoded JSON fragments, submitted keys, or parser context through `__cause__`.

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

Delivery smoke XML exports use the same exclusive-create local artifact writer as JSON audit artifacts. Existing files, existing symlinks, and broken symlinks at the generated export path are rejected before XML content is written, so smoke runs cannot overwrite prior exports or redirect XML outside the configured artifact root.

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

Each batch writes a write-once batch report artifact named after `--execution-id`. The report includes capability status, summary counts, and per-story outcome records. It does not include ServiceNow sys_ids. Batch reports are sanitized diagnostic projections: execution ids, actor ids, capability reasons, result reasons, audit paths, story numbers, and nested exact string values are redacted for credential-like fragments, normalized for whitespace/control characters, and bounded before JSON artifact output. Batch report diagnostic keys are projected before output as well: exact string keys are sanitized through the same writeback field-value boundary, while non-string keys render as `[non-json key]` without calling `str()` or `repr()` on malformed key objects. If multiple diagnostic keys render to the same sanitized key, later entries receive deterministic `[duplicate N]` suffixes instead of overwriting earlier evidence. Batch report diagnostic traversal is also cycle-safe and depth-bounded; repeated containers render as `[circular reference]`, and containers beyond the diagnostic depth cap render as `[max depth exceeded]`. Batch reports traverse only exact dictionaries, lists, and tuples; dictionary, list, and tuple subclasses render as `[non-json value]` before `items()`, `len()`, iteration, or subclass hooks can execute. Unsupported diagnostic scalar values, string subclasses, binary values, objects, and non-finite floats render as `[non-json value]`; finite JSON primitives remain typed. Batch report boolean and integer diagnostic values must be exact JSON scalar types; boolean and integer subclasses render as `[non-json value]` instead of being preserved as ordinary report booleans or numbers.

ServiceNow Table API `result` payloads are validated at the container boundary before record or object traversal. Result lists must be exact `list` instances and result entries must be exact `dict` instances; singleton result objects must also be exact dictionaries. Ordinary malformed JSON payloads keep the stable operator diagnostics for non-list or non-object shapes, while Python subclass payloads introduced through internal seams fail with exact-container diagnostics before iterator, `get()`, `items()`, `str()`, or `repr()` hooks can execute or leak credential-like payloads.

ServiceNow Table API mutation field bodies are validated before request construction. Story-field updates and generic table upserts require the submitted field body to be an exact dictionary before field-name sanitization, OAuth token acquisition, lookup queries, PATCH requests, or POST requests. Dict subclasses and non-dictionary values fail with `ServiceNow API field body must be an exact dictionary` before `items()`, stringification, or credential-bearing subclass hooks can execute.

ServiceNow Table API lookup bodies are also validated before query construction. Table-record lookups, table-record list queries, and generic table upserts require the submitted lookup body to be an exact dictionary before lookup key/value sanitization, OAuth token acquisition, GET requests, or mutation requests. Dict subclasses and non-dictionary lookup bodies fail with `ServiceNow API lookup body must be an exact dictionary` before `items()`, stringification, or credential-bearing subclass hooks can execute.

ServiceNow Table API `sysparm_fields` lists are validated before field-list query construction. Table-record list queries require the optional `fields` argument to be an exact list before field-name sanitization, OAuth token acquisition, or GET request construction. List subclasses and non-list field containers fail with `ServiceNow API field list must be an exact list` before iteration, stringification, or credential-bearing subclass hooks can execute.

ServiceNow Table API result limits are validated before query construction. Story queries and table-record list queries require `limit` to be an exact integer in the supported range before comparison, string conversion, OAuth token acquisition, or GET request construction. Boolean values, integer subclasses, non-integers, zero, negative values, and oversized values fail with `ServiceNow API result limit is unsafe` without echoing submitted values or executing comparison/stringification hooks.

ServiceNow dictionary field max lengths are validated before dictionary-field request construction. `create_story_dictionary_field()` requires `max_length`, when supplied, to be an exact integer in the supported ServiceNow dictionary range before comparison, string conversion, OAuth token acquisition, or POST request construction. Boolean values, integer subclasses, non-integers, zero, negative values, and oversized values fail with `ServiceNow dictionary max length is unsafe` without echoing submitted values or executing comparison/stringification hooks.

ServiceNow lookup response text is validated before reuse in follow-on requests. Generic table upsert reads the existing-record `sys_id` through a scalar boundary that accepts only null, exact strings, exact booleans, and exact integers before record-id validation. String subclasses, integer subclasses, arbitrary objects, and other non-JSON scalar values fail with `ServiceNow API lookup response value is not JSON-safe` before string conversion, PATCH URL construction, or credential-bearing subclass hooks can execute.

ServiceNow transport query parameters are validated before URL construction. `UrllibTransport` requires `HttpRequest.params` to be an exact dictionary before checking whether parameters are empty or passing them to URL encoding. Dict subclasses and non-dictionary parameter containers fail with `ServiceNow request query params must be an exact dictionary` before truthiness checks, iteration, URL encoding, opener construction, or credential-bearing subclass hooks can execute.

ServiceNow transport query parameter keys and values are validated before URL encoding. After the exact-dictionary container check, every `HttpRequest.params` entry must have an exact string key and exact string value before `urllib.parse.urlencode()` is called. String subclasses and non-string query scalars fail with `ServiceNow query params must contain exact string keys and values` before URL encoding, implicit string conversion, opener construction, or credential-bearing scalar hooks can execute.

ServiceNow transport methods and URLs are validated before request construction. `UrllibTransport` requires `HttpRequest.method` to be an exact uppercase method from the supported transport set: `GET`, `POST`, `PATCH`, `PUT`, or `DELETE`. Unsafe methods fail with `ServiceNow request method is unsafe` before raw `urllib` request construction. `HttpRequest.url` must be an exact absolute HTTP or HTTPS URL no longer than 4096 characters, with no whitespace or control characters, no decoded whitespace/control characters, no embedded credentials, and no fragment. Unsafe URLs fail with `ServiceNow request URL is unsafe` before query encoding, raw request construction, opener construction, or credential-bearing scalar hooks can execute.

ServiceNow transport request bodies are validated before body encoding. `UrllibTransport` requires `HttpRequest.body` to be an exact dictionary when no raw `body_bytes` payload is supplied. Dict subclasses and non-dictionary body containers fail with `ServiceNow request body must be an exact dictionary` before truthiness checks, JSON serialization, form encoding, opener construction, or credential-bearing subclass hooks can execute. Raw attachment uploads continue to use `body_bytes` and bypass dictionary body encoding.

ServiceNow transport headers are validated before request construction. `UrllibTransport` requires `HttpRequest.headers` to be an exact dictionary before copying headers, reading `Content-Type`, JSON serialization, form encoding, opener construction, or raw `urllib` request construction. Dict subclasses and non-dictionary header containers fail with `ServiceNow request headers must be an exact dictionary` before credential-bearing subclass hooks can execute.

ServiceNow transport header keys and values are validated before request construction. After the exact-dictionary container check, every `HttpRequest.headers` entry must have an exact string key and exact string value before header copying, `Content-Type` lookup, raw `urllib` request construction, or opener construction. String subclasses and non-string header scalars fail with `ServiceNow request headers must contain exact string keys and values` before credential-bearing scalar hooks can execute.

ServiceNow transport raw body bytes are validated before request construction. `UrllibTransport` requires `HttpRequest.body_bytes` to be exact bytes when supplied, so attachment uploads and other raw payload paths cannot pass bytes subclasses or non-byte containers into raw `urllib` request construction. Malformed raw body payloads fail with `ServiceNow request body bytes must be exact bytes` before opener construction, request construction side effects, or credential-bearing subclass hooks can execute.

ServiceNow transport form request bodies are validated before URL encoding. When `UrllibTransport` sends a non-JSON dictionary body without raw `body_bytes`, every form field must have exact string keys and exact string values before `urllib.parse.urlencode()` is called. String subclasses, non-string keys, and non-string values fail with `ServiceNow form request body must contain exact string keys and values` before URL encoding, implicit string conversion, opener construction, or credential-bearing scalar hooks can execute.

ServiceNow transport URL encoding runs through a safe boundary. Query parameter dictionaries and form body dictionaries are validated to exact string keys and values before `urllib.parse.urlencode()` executes, and unexpected URL-encoding failures become `ServiceNow transport URL encoding failed` without stringifying or chaining the original exception. This prevents malformed local urllib adapters from leaking credential-bearing encoder diagnostics before raw request construction or opener execution begins.

ServiceNow transport response status values are validated before HttpResponse construction. Successful urllib response `status` values and HTTP error `code` values must be exact integers in the HTTP `100..599` range before the transport constructs an internal `HttpResponse`. Boolean values, integer subclasses, non-integers, and out-of-range values fail with `ServiceNow transport response status must be an exact HTTP status code` before model coercion, downstream response branching, or credential-bearing status hooks can execute.

ServiceNow transport response status is validated before body reads. The urllib transport checks successful response `status` and HTTP error `code` values before calling `.read()` on response bodies. Malformed status values fail with `ServiceNow transport response status must be an exact HTTP status code` before body streaming, oversized-body checks, decoding, diagnostic shaping, or credential-bearing body read hooks can execute.

ServiceNow transport response status attributes are read through a safe boundary. Successful response `status` and HTTP error `code` attribute lookup failures are converted to `ServiceNow transport response status must be an exact HTTP status code` without stringifying the response object, exception object, or attribute failure. This prevents malformed transport adapters from leaking credential-bearing attribute hooks before status validation, body reads, or diagnostic shaping.

ServiceNow transport timeout values are validated before opener execution. Direct `UrllibTransport(timeout_seconds=...)` construction accepts only exact integer or float values that are finite, greater than zero, and no more than 300 seconds before the value can reach `opener.open()`. Boolean values, numeric subclasses, non-numeric values, non-finite values, zero, negative values, and oversized values fail with `ServiceNow transport timeout must be a finite positive number` before network execution or credential-bearing numeric hooks can execute.

ServiceNow transport response body reads are validated before decoding. Successful urllib response bodies and HTTP error response bodies must be exact `bytes` immediately after `.read()` returns and before length checks, UTF-8 decoding, JSON parsing, diagnostic shaping, or `HttpResponse` construction. Bytes subclasses and non-byte response bodies fail with `ServiceNow transport response body must be exact bytes` before credential-bearing decode hooks can execute.

ServiceNow transport successful-response JSON parse diagnostics do not retain unsafe causes.
Successful response bodies that fail UTF-8 decoding fail with
`ServiceNow API response body is not valid UTF-8 JSON`, and successful response bodies that fail JSON
parsing or non-finite JSON numeric rejection fail with
`ServiceNow API response body is not valid JSON`. Those public `ServiceNowApiError` instances
suppress decoder and parser exceptions, so crash reporters, traceback formatters, and work-note
writers do not retain response-derived field names, response byte snippets, JSON token fragments, or
credential-bearing parser context in `__cause__`.

ServiceNow transport response body reads execute through a safe boundary. Successful urllib response body reads and HTTP error response body reads are wrapped before exact-bytes validation. Read attribute failures, socket read failures, malformed response adapters, and other read-time exceptions fail with `ServiceNow transport response body read failed` without stringifying or chaining the original exception. This prevents response body read failures from leaking credential-bearing exception text before oversized-body checks, decoding, JSON parsing, diagnostic shaping, or `HttpResponse` construction.

ServiceNow transport response context managers execute through a safe boundary. Successful urllib response context `__enter__` and `__exit__` execution is wrapped with `ServiceNow transport response context failed` before response status validation, body reads, JSON parsing, or `HttpResponse` return. Context-manager failures are not stringified or chained, so malformed response adapters cannot leak credential-bearing context hook text while opening or closing response resources.

ServiceNow transport opener execution runs through a safe boundary. The raw `opener.open()` call is wrapped before response context handling, status validation, body reads, JSON parsing, or `HttpResponse` construction. Unexpected opener execution failures, including hostile `open` attribute lookup failures, become `ServiceNow transport request failed` without stringifying or chaining the original exception. HTTP error responses remain on the bounded HTTP error path for status and body handling.

ServiceNow transport opener construction runs through a safe boundary. The urllib opener is built through a fixed diagnostic wrapper before request execution. Unexpected `urllib.request.build_opener()` failures become `ServiceNow transport request failed` without stringifying or chaining the original exception, so malformed local transport adapters cannot leak credential-bearing construction diagnostics before network execution begins.

ServiceNow transport request construction runs through a safe boundary. After method, URL, header, body, query, and timeout validation, the raw `urllib.request.Request(...)` object is constructed through a fixed diagnostic wrapper. Unexpected request-construction failures become `ServiceNow transport request failed` without stringifying or chaining the original exception, so malformed local urllib adapters cannot leak credential-bearing constructor diagnostics before opener construction or network execution begins.

ServiceNow transport network failures are wrapped before leaving the transport. Non-HTTP urllib failures and local socket or TLS `OSError` failures are converted to `ServiceNow transport request failed` without reading, stringifying, or chaining the original exception. HTTP error responses remain on the bounded HTTP error path. This keeps DNS, connection, timeout, socket, and TLS diagnostics from leaking URL fragments, local proxy details, credential-bearing reason strings, or exception-object hooks into operator logs or work notes.
