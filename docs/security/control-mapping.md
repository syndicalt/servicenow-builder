# Security Control Mapping

This draft maps implemented controls to practical engineering evidence. It is not an ATO package.
Control selection, inheritance, and customer-specific overlays remain part of the customer
authorization process.

## Implemented Controls

| Control Area | Implemented Control | Code Evidence | Test Evidence |
|---|---|---|---|
| Inbound authentication | HMAC-SHA256 lifecycle webhook signatures over `<timestamp>.<raw body>`; constant-time comparison; hex and ServiceNow Base64 signature shapes; shared-secret interim mode; unconfigured modes fail closed with `503`. | `lifecycle_api.py`, `lifecycle_webhook_policy.py` | `tests/test_lifecycle_api.py` |
| Replay protection | Timestamp replay window, default 300 s; production configuration capped at 900 s. | `lifecycle_api.py`, `runtime_config.py` | `tests/test_lifecycle_api.py` |
| Secret rotation | `JEDI_LIFECYCLE_WEBHOOK_PREVIOUS_SECRET` overlap window; previous secret must differ from the active secret. | `lifecycle_api.py`, `runtime_config.py` | `tests/test_lifecycle_api.py`, `tests/test_runtime.py` |
| Denial-of-service bounds | Streaming request body caps (lifecycle default 64 KiB, admin default 8 KiB); per-process sliding-window rate limiters with `429` + `Retry-After`; bounded limiter bucket cardinality; admin list limits capped at 100 rows. | `lifecycle_api.py`, `admin_routes.py`, `rate_limit.py` | `tests/test_rate_limit.py`, `tests/test_runtime.py` |
| Fail-closed configuration | Production startup validation rejects missing or malformed webhook secrets, admin tokens, trusted hosts, HSTS, database URLs, ServiceNow URLs, provider settings, and out-of-range numeric bounds before serving traffic. | `runtime_config.py`, `admin_routes.py` | `tests/test_runtime.py`, `tests/test_runtime_entrypoints.py` |
| Admin access control | Bearer token for JSON admin/artifact APIs with `secrets.compare_digest`; `JEDI_ADMIN_AUTH_MODE=disabled` default; `dev_basic` restricted to development; reserved OIDC/ServiceNow OAuth modes fail closed with `501`. | `runtime_auth.py`, `admin_token_policy.py`, `admin_basic_auth_policy.py` | `tests/test_runtime.py` |
| Least-privilege ServiceNow access | Split PM/DEV OAuth clients; read-only surface discovery; writeback limited to allowlisted `rm_story` fields and discovered state transitions; `JEDI_BUILD_CLAIM_APPLY` and `JEDI_UPDATE_SET_APPLY` default to `false`. | `servicenow.py`, `runtime_servicenow.py`, `writeback.py`, `writeback_orchestration.py` | `tests/test_writeback.py`, `tests/test_writeback_audit.py`, `tests/test_writeback_orchestration.py` |
| Credential handling in transit | No-redirect HTTP transport for all ServiceNow calls; OAuth token responses validated as exact ASCII strings before caching; HTTPS-only instance URLs without embedded credentials. | `servicenow.py`, `runtime_config.py` | `tests/test_runtime.py` |
| Secret protection at rest and in source | `.env` git-ignored; `.env.example` carries key names only; secrets live in the hosting environment; production secrets meet minimum length and character rules at startup. | `.gitignore`, `.env.example`, `runtime_config.py` | `tests/test_runtime.py` |
| Redaction | Literal secret replacement in handler errors; diagnostic redaction of URLs, authorization headers, cookies, PEM keys, and sensitive assignments; work-note sanitization; recursive sensitive-key redaction in admin artifact views. | `runtime_redaction.py`, `diagnostic_redaction.py`, `sensitive_keys.py`, `literal_secret_values.py`, `work_note_safety.py`, `admin_routes.py` | `tests/test_runtime_redaction.py`, `tests/test_runtime_control_dto_redaction.py`, `tests/test_operational_dto_redaction.py` |
| Error reflection prevention | Webhook validation errors omit submitted input values; public errors do not chain parser or validation exceptions; readiness probes return check names only. | `lifecycle_api.py`, `admin_routes.py` | `tests/test_lifecycle_api.py`, `tests/test_runtime.py` |
| SSRF and egress control | Alert webhook URLs validated (HTTPS, no credentials, no local/link-local targets, no sensitive query keys); provider base URLs validated (HTTPS public host, no credentials/query/fragment); public web access disabled by default and allowlist-only when enabled. | `alert_webhook_url.py`, `url_host_safety.py`, `url_query_safety.py`, `provider_url_safety.py`, `runtime_config.py` | `tests/test_alert_webhook_url.py`, `tests/test_url_query_safety.py`, `tests/test_provider_settings_safety.py` |
| Boundary control for model calls | Default provider policy approves only the local rules-only provider; production requires an explicit provider with credentials; provider responses validated against a strict structured contract. | `security_defaults.py`, `providers.py`, `provider_contract.py`, `runtime_config.py` | `tests/test_security_defaults.py`, `tests/test_provider_contract.py`, `tests/test_openai_provider.py` |
| Data minimization | Model-facing implementation packets use minimized story fields, redacted script-like fields, citation-backed context, and sys_id minimization. | `implementation_packet.py`, `packet_context.py` | `tests/test_runtime_control_dto_redaction.py` |
| Generated-output safety | Model output is structured candidate data validated against allowlisted tables and operations; raw XML from a model fails closed; retrieved Update Set XML comes only from deterministic builders for mature surfaces; human preview and commit stay in ServiceNow. | `packet_validation.py`, `update_set_handoff.py`, generation modules | `tests/test_atf_test_generation.py`, capability and generation test modules |
| Auditability | `lifecycle_events` preserves raw inbound payloads; `job_events` is append-only; `artifact_refs` records SHA-256 hashes; every response carries `X-JEDI-Request-ID`; failure work notes include event and job ids. | `operational_store.py`, `admin_routes.py`, `runtime_servicenow.py` | `tests/test_operational_store.py`, `tests/test_fulfillment_worker.py` |
| Injection resistance | Parameterized SQL through psycopg; exact-shape and exact-scalar guards on every row the store returns before hydration. | `operational_store.py` | `tests/test_operational_store.py` |
| Transport security headers | HSTS required for public production roles (`max-age >= 31536000`); `X-Content-Type-Options: nosniff` on all responses; `no-store` cache controls and restrictive CSP/frame/referrer/permissions policies on admin routes. | `admin_routes.py`, `runtime_config.py` | `tests/test_runtime.py` |
| Host header validation | `JEDI_TRUSTED_HOSTS` required for public production roles; enforced through Starlette `TrustedHostMiddleware`. | `admin_routes.py`, `runtime_config.py` | `tests/test_runtime.py` |
| Test evidence | Ruff lint, bandit, pip-audit, mypy strict typing, and pytest with a 90% coverage gate; combined in the `verify` command under `tool.jedi-devproject.commands`. | `pyproject.toml` | `verify` quality gate |

## Deployment-Held Controls

Some controls are deliberately the responsibility of the hosting environment, not this codebase:

- Distributed rate limiting, request size limits, IP reputation, and WAF enforcement at a
  customer-approved edge or API gateway. The in-process limiter is per-process only.
- Secret manager integration, rotation scheduling, and custodian records beyond the webhook
  previous-secret overlap window.
- Encryption at rest for PostgreSQL and object storage, database backup, and retention execution.
  Retention runbook guidance is in `docs/operator-guide.md` under "Operational Store Retention".
- TLS termination and certificate management in front of the runtime API.

## Open Control Work

Open control work remains before production use: customer ATO control mapping and inheritance,
approved storage and vector-store selection, retention policy execution, role-backed admin identity
(OIDC or ServiceNow OAuth — see `docs/admin-auth-config.md`), and an incident response process.
