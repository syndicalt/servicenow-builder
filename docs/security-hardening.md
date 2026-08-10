# Security Hardening

Production security posture for the JEDI DevProject sidecar: request bounds, the fail-closed
production checklist, and the secret inventory with rotation paths. For the runtime
configuration values these controls constrain, see the Runtime Wiring section of
`docs/runtime-operations.md`; lifecycle webhook HMAC authentication is documented with the
Lifecycle Webhook API in the same guide. For container, compose, and image hardening, see
`docs/installation.md`.

## Contents

- [Rate Limits and Payload Bounds](#rate-limits-and-payload-bounds) — per-process body-size ceilings, rate limits, and trusted hosts.
- [Production Runtime Fail-Closed Checklist](#production-runtime-fail-closed-checklist) — required production settings and startup validation.
- [Secret Inventory](#secret-inventory) — secret locations, purposes, and rotation paths.

## Rate Limits and Payload Bounds

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

## Production Runtime Fail-Closed Checklist

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

## Secret Inventory

| Secret | Location | Purpose | Rotation Path |
|---|---|---|---|
| `SERVICENOW_CLIENT_SECRET` | API and worker runtime env | ServiceNow OAuth client credentials for Table API operations | Rotate the ServiceNow OAuth app secret, update runtime env, redeploy API and worker |
| `JEDI_LIFECYCLE_WEBHOOK_SECRET` | API runtime env | HMAC validation for inbound lifecycle events | Generate a new random value, update API env and ServiceNow `x_jedi.lifecycle.webhook.secret`, then redeploy/retest signed webhook calls |
| `x_jedi.lifecycle.webhook.secret` | ServiceNow system property | HMAC signing secret read by the lifecycle Business Rule emitter | Match `JEDI_LIFECYCLE_WEBHOOK_SECRET`; update out of band and do not place the value in bootstrap artifacts |
| `OPENAI_API_KEY` | Worker runtime env | ChatGPT/OpenAI model execution | Rotate in the approved OpenAI project, update worker env, redeploy worker, and run a model smoke story |
| `ANTHROPIC_API_KEY` | Worker runtime env | Anthropic model execution when that adapter is explicitly configured | Rotate in the approved Anthropic account or gateway, update worker env, redeploy worker, and run a model smoke story |
| `JEDI_ADMIN_CONSOLE_PASSWORD` | API runtime env, development only | Local Basic auth for `/admin` during development | Replace with a strong temporary value when needed; do not use with `JEDI_ENVIRONMENT=production` |
| `JEDI_ADMIN_API_TOKEN` | API runtime env | Bearer token for JSON artifact/admin diagnostic API endpoints | Rotate by updating the API env and all approved operator clients |
