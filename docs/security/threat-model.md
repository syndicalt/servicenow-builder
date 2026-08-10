# Threat Model

## Scope

This threat model covers the hosted JEDI DevProject sidecar runtime: the FastAPI lifecycle/admin
API, the fulfillment worker, the PostgreSQL operational store, outbound ServiceNow Table API and
OAuth traffic, model provider calls, alert egress, and the read-only admin console. The canonical
component and trust-boundary diagrams live in `docs/system-architecture.md`; this file enumerates
threats and maps each one to the control that mitigates it.

Local development posture and fixture rules are covered by
`docs/policies/local-regulated-data.md`. Admin identity configuration is covered by
`docs/admin-auth-config.md`.

## Assets

- ServiceNow OAuth client credentials for the PM/source and DEV/target instances
  (`SERVICENOW_PM_CLIENT_SECRET`, `SERVICENOW_DEV_CLIENT_SECRET`, legacy `SERVICENOW_CLIENT_SECRET`).
- Lifecycle webhook signing secret (`JEDI_LIFECYCLE_WEBHOOK_SECRET`, plus
  `JEDI_LIFECYCLE_WEBHOOK_PREVIOUS_SECRET` during rotation).
- Admin API bearer token (`JEDI_ADMIN_API_TOKEN`) and development admin console credentials.
- Model provider credentials (`OPENAI_API_KEY`).
- `DATABASE_URL` and the PostgreSQL operational store contents: lifecycle event payloads,
  fulfillment jobs, job events, artifact blobs, and artifact refs.
- `rm_story` content and related project, instance-metadata, and compliance context.
- Generated artifacts: implementation packets, context dossiers, candidates, retrieved Update Set
  XML, intake feedback, and ATF test plans.
- Reviewer decisions, audit records, and ServiceNow work notes written by the runtime.

## Trust Boundaries

| Boundary | Controls |
|---|---|
| ServiceNow lifecycle emitter to Runtime API | HMAC-SHA256 webhook signature, timestamp replay window, body size cap, per-process rate limit, strict payload schema. |
| Runtime API to PostgreSQL | Parameterized SQL, transaction boundaries, exact-shape row guards, immutable event payload preservation. |
| Worker to PM ServiceNow instance | OAuth client credentials over HTTPS, no-redirect transport, allowlisted `rm_story` writeback fields, discovered state choices. |
| Worker to DEV ServiceNow instance | Separate OAuth credentials, read-only surface discovery, reviewed importer endpoint, retrieved Update Set handoff only for mature builders. |
| Worker to model provider | Provider policy gate, data-classification gate, minimized citation-backed packet, strict JSON output contract, raw XML rejection. |
| Worker to alert webhook sink | HTTPS-only validated URL, bounded body and timeout, disabled by default. |
| Worker to public web (optional) | Disabled by default; domain allowlist, HTTPS-only, bounded responses when enabled. |
| Admin browser or client to Runtime API | Bearer token for JSON diagnostics, development-only Basic auth for the HTML console, admin rate limit, trusted-host middleware, security headers. |

## Threats and Mitigations

### Inbound webhook threats

| Threat | Mitigation | Code evidence |
|---|---|---|
| Forged lifecycle events | `hmac_sha256` mode verifies `HMAC-SHA256` over `<timestamp>.<raw body>` with `hmac.compare_digest`; required for production API-serving roles. | `lifecycle_api.py`, `runtime_config.py` |
| Replay of captured events | `X-JEDI-Webhook-Timestamp` must sit inside the replay window (default 300 s; production caps configuration at 900 s). | `lifecycle_api.py` |
| Secret rotation downtime or ambiguity | `JEDI_LIFECYCLE_WEBHOOK_PREVIOUS_SECRET` overlap window; previous secret must differ from the active secret; comparisons do not disclose which secret matched. | `lifecycle_api.py`, `runtime_config.py` |
| Credential probing with malformed headers | Timestamp, signature, and shared-secret headers must be ASCII, unpadded, whitespace- and control-free, and at most 8 KiB before parsing or comparison. | `lifecycle_webhook_policy.py` |
| Unauthenticated deployment | `disabled` auth mode returns `503` on every request; production startup requires `hmac_sha256` for API-serving roles (`combined`, `api`) and rejects webhook settings entirely on `worker`-only services. `servicenow_oauth` is reserved and returns `501`. | `lifecycle_api.py`, `runtime_config.py` |
| Oversized payload denial of service | Request body is capped while streaming (default 64 KiB; production ceiling 1 MiB) before JSON parsing, HMAC validation, or store writes; oversized bodies get `413`. | `lifecycle_api.py` |
| Request flood | In-memory sliding-window rate limiter keyed by client host and path returns `429` with `Retry-After`; bucket cardinality is capped and long/unicode keys are hashed. | `rate_limit.py`, `lifecycle_api.py` |
| Payload reflection in error responses | Validation errors omit Pydantic `input` values; malformed JSON and non-finite JSON numbers fail with a fixed `invalid lifecycle webhook JSON` diagnostic; public errors do not chain parser exceptions. | `lifecycle_api.py`, `admin_routes.py` |

The rate limiter is a per-process control, not a distributed abuse boundary. Production deployments
must also enforce request size, rate, and IP reputation at a customer-approved edge, WAF, or API
gateway.

### Secret and credential threats

| Threat | Mitigation | Code evidence |
|---|---|---|
| Secret leakage into logs, exceptions, or work notes | Literal configured secrets (database URL and password, ServiceNow client secrets, webhook secrets) are replaced with `***REDACTED***` before handler errors propagate; diagnostic text redacts URLs with credentials, sensitive query keys, `Authorization` values, cookies, PEM private keys, and sensitive key assignments; work-note values are redacted, whitespace-normalized, and capped at 500 chars. | `runtime_redaction.py`, `diagnostic_redaction.py`, `work_note_safety.py`, `literal_secret_values.py`, `sensitive_keys.py` |
| Credential forwarding via HTTP redirect | The urllib transport installs a no-redirect opener; OAuth, Table API, and Attachment API calls never follow 3xx responses, so bearer tokens cannot leak to another host. | `servicenow.py` (`_NoServiceNowRedirectHandler`) |
| Malformed tokens becoming credentials | OAuth token responses must be exact ASCII strings, unpadded, control-free, and at most 8 KiB before caching; diagnostics never echo token material. | `servicenow.py` |
| Secrets in source control | `.env` is git-ignored; `.env.example` ships key names only; production secrets belong in the hosting environment or an approved secret manager. | `.gitignore`, `.env.example` |
| Misconfigured ServiceNow or database targets | Startup validation requires HTTPS instance URLs without embedded credentials, fragments, or whitespace/control characters, and a PostgreSQL `DATABASE_URL` without fragments. | `runtime_config.py` |

### Outbound and server-side request forgery threats

| Threat | Mitigation | Code evidence |
|---|---|---|
| Alert webhook used as SSRF channel | Alert URLs must be HTTPS, credential-free, fragment-free, free of sensitive query parameters, and must not target local or link-local addresses (including legacy IPv4 encodings and unicode dot aliases). Delivery is disabled by default with bounded body and timeout. | `alert_webhook_url.py`, `url_host_safety.py`, `alert_delivery.py` |
| Provider endpoint redirected inside the boundary | Provider base URLs must be absolute HTTPS URLs with a public hostname, no credentials, no query, and no fragment. | `provider_url_safety.py` |
| Public web retrieval abuse | `JEDI_PUBLIC_WEB_ACCESS` defaults to `disabled`; `worker` mode requires an explicit domain allowlist and doc URL list, uses HTTPS only, and bounds response size, excerpt length, result count, and timeout. | `runtime_config.py` |

### Admin surface threats

| Threat | Mitigation | Code evidence |
|---|---|---|
| Unauthenticated diagnostic access | JSON admin and artifact endpoints require `Authorization: Bearer <JEDI_ADMIN_API_TOKEN>` checked with `secrets.compare_digest`; a missing or malformed configured token fails closed with `503`. | `runtime_auth.py`, `admin_token_policy.py` |
| Browser console exposure in production | `JEDI_ADMIN_AUTH_MODE` defaults to `disabled` (console returns `503`); `dev_basic` is rejected outside `JEDI_ENVIRONMENT=development` at both startup and request time; `oidc` and `servicenow_oauth` return `501` until implemented. | `runtime_auth.py`, `runtime_config.py` |
| Basic-auth credential attacks | Basic credentials must decode cleanly, be unpadded ASCII without control characters, and are compared with `secrets.compare_digest`; failures return `401` with a fixed `WWW-Authenticate` realm. | `runtime_auth.py`, `admin_basic_auth_policy.py` |
| XSS in the admin console | All dynamic values are HTML-escaped; console responses carry `Content-Security-Policy: default-src 'none'; script-src 'none'`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, and a restrictive `Permissions-Policy`. | `admin_routes.py` |
| Artifact payload secrets in admin views | Admin artifact rendering recursively redacts sensitive keys, bounds depth (32), item count (100), and total size (16 KiB), and marks truncation. | `admin_routes.py`, `sensitive_keys.py` |
| Response caching of diagnostics | Admin diagnostic routes send `Cache-Control: no-store`, `Pragma: no-cache`, `Expires: 0`, `X-Robots-Tag: noindex`, and `Vary: Authorization`. | `admin_routes.py` |
| Host header attacks | Production public roles must configure `JEDI_TRUSTED_HOSTS`; Starlette `TrustedHostMiddleware` rejects unexpected Host headers. | `admin_routes.py`, `runtime_config.py` |
| Protocol downgrade | `JEDI_STRICT_TRANSPORT_SECURITY_ENABLED=true` with `max-age >= 31536000` is required for public production roles; all responses send `X-Content-Type-Options: nosniff`. | `admin_routes.py`, `runtime_config.py` |
| Request id log injection | Inbound `X-Request-ID` is echoed as `X-JEDI-Request-ID` only when it is printable ASCII up to 128 chars; otherwise a UUID4 is generated. | `admin_routes.py` |

### Data and pipeline threats

| Threat | Mitigation | Code evidence |
|---|---|---|
| Unauthorized model calls | The default provider policy approves only the local `rules-only` provider for `classify_story` on public data; production requires an explicit `JEDI_MODEL_PROVIDER` with credentials. | `security_defaults.py`, `runtime_config.py` |
| Regulated data sent to a model | Model-facing payloads use the minimized implementation packet: no ServiceNow sys_ids unless required, redacted script-like fields, citation-backed context, and a data-classification gate. | `implementation_packet.py`, `docs/system-architecture.md` |
| Model output becoming direct platform change | Model output is structured candidate data validated against allowlisted tables and operations; raw XML from a model fails closed. XML is produced only by deterministic builders for mature surfaces. | `packet_validation.py`, `docs/system-architecture.md` |
| Uncontrolled ServiceNow mutation | Writeback is limited to allowlisted `rm_story` fields and discovered state transitions; `JEDI_BUILD_CLAIM_APPLY` and `JEDI_UPDATE_SET_APPLY` default to `false`; retrieved Update Sets require human preview, scan, and commit in ServiceNow. | `writeback.py`, `writeback_orchestration.py`, `runtime_config.py` |
| SQL injection through operational records | The operational store uses parameterized queries through psycopg with exact-shape, exact-scalar row guards before any record is hydrated. | `operational_store.py` |
| Silent estimate or review-state mutation | Repointing is advisory with evidence; reviewer decisions and job state changes are append-only `job_events`; rejected stories preserve artifacts for audit. | `docs/system-architecture.md`, `operational_store.py` |
| Alert delivery failing closed on operators | Alert delivery failure is logged with redacted diagnostics and never blocks lifecycle processing; rejected-job alerts carry bounded payloads. | `lifecycle_api.py`, `alert_delivery.py` |

## Fail-Closed Defaults

- `JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE=disabled`: every webhook call returns `503`.
- `JEDI_ADMIN_AUTH_MODE=disabled`: browser console returns `503`; JSON diagnostics require the bearer token.
- `JEDI_MODEL_PROVIDER` unset in production: startup fails for worker-capable roles.
- `JEDI_ALERT_WEBHOOK_ENABLED=false`: no alert egress.
- `JEDI_PUBLIC_WEB_ACCESS=disabled`: no public web retrieval.
- `JEDI_BUILD_CLAIM_APPLY=false` and `JEDI_UPDATE_SET_APPLY=false`: no state-claim or Update Set mutation.
- `JEDI_CLASSIFIER_GATE=true`: classifier gate enforced; `false` is development-only.
- Invalid rate-limit, body-limit, or alert settings raise `RuntimeConfigError` before the API serves traffic.

The full production startup checklist is maintained in `docs/operator-guide.md` under
"Production Runtime Fail-Closed Checklist".

## Residual Risk and Open Control Work

- Admin identity is bearer-token or development Basic auth until OIDC or ServiceNow OAuth is
  implemented; see `docs/admin-auth-config.md`.
- Rate limiting is per-process; a distributed edge control is a deployment responsibility.
- The Anthropic provider adapter exists at contract parity but is not wired into runtime provider
  selection; any provider use still requires policy approval.
- Customer ATO control mapping, approved storage and retention configuration, identity controls,
  and incident response process remain customer-side work before production authorization.
