# Installation

Deploy the JEDI DevProject sidecar runtime: local environment configuration, the container
stack, and the hosted process split. For the runtime architecture, workflow diagrams, and
data-flow diagrams, see `docs/system-architecture.md`. For local verification and smoke
workflows, see `docs/local-development.md`. For operating the deployed services, see
`docs/runtime-operations.md`. For the production security posture, see
`docs/security-hardening.md`.

## Contents

- [Local Configuration](#local-configuration) — `.env` credentials, env-file and project-config parsing boundaries, and Docker build-context exclusions.
- [Container Runtime](#container-runtime) — `Dockerfile`, `Dockerfile.worker`, and `docker-compose.yml` services, container hardening, and worker loop controls.
- [Hosted Railway Process Split](#hosted-railway-process-split) — API and worker service manifests and per-service secret placement.
- [Runtime Role Boundary](#runtime-role-boundary) — `api`, `worker`, and `combined` role validation.

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
