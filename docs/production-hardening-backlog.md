# Production Hardening Backlog

## Sprint 101 Cut Line

Sprint 101 is the MVP cut line. The MVP proves the end-to-end product shape: ServiceNow lifecycle events enqueue asynchronous fulfillment, the worker generates reviewed retrieved Update Set handoffs for supported dictionary/form stories, Ready for Testing is written back, UAT closeout/rework/rejection events are captured, PostgreSQL stores operational state, and `/admin` provides read-only visibility.

Post-101 work is production hardening. The rule for this phase is **No new mutation surface** until authentication, observability, evidence, and review controls are stronger.

## Hardening Principles

- Tests first, always.
- No hacks; re-engineer weak boundaries instead of patching around them.
- ServiceNow remains the work surface.
- Retrieved Update Set preview/commit remains the human review boundary.
- Admin console remains read-only until operator actions are separately designed.
- Every sprint must leave a clearer security posture than it started with.

## Production Hardening Backlog

| Priority | Sprint | Backlog Item | Why It Matters | Exit Criteria |
|---:|---|---|---|---|
| 1 | Sprint 102 | Admin auth strategy boundary | Local Basic auth is acceptable for the MVP but not the production operator identity model, and ServiceNow browser-session role checks are not safe to assume under SSO. | `/admin` fails closed by default, Basic auth is explicitly development-only, and future `oidc` and `servicenow_oauth` modes are documented but not enabled until implemented. |
| 2 | Sprint 103 | Authenticated inbound lifecycle webhook | The current PDI bootstrap history includes `no_authentication`; production cannot accept public lifecycle events without request authentication. | `/lifecycle/events` rejects unauthenticated calls. ServiceNow emits lifecycle events with a signed secret, OAuth-authenticated REST message, or another approved mechanism. Replay and malformed-signature tests are present. |
| 3 | Sprint 104 | Confidence-based context retrieval worker | Deterministic context escalation exists, but the runtime still needs the actual retrieval step before model generation. | Missing live instance context claims a retrieval task before model execution. Insufficient retrieved context routes to human review. The model is never asked to infer unavailable ServiceNow shape. |
| 4 | Sprint 105 | Admin console drill-down and evidence views | Operators need diagnostics without database access, but the console should remain read-only. | Job detail, lifecycle event detail, artifact detail, retrieved Update Set links, and failure summaries are visible. No retry/rebuild/commit controls exist. |
| 5 | Sprint 106 | ATO evidence refresh | Security docs still describe the early MVP path more than the current hosted sidecar. | Data flow, threat model, control mapping, risk register, and sprint evidence index reflect Railway dev hosting, PostgreSQL artifacts, ChatGPT evaluation, ServiceNow webhook, and retrieved Update Set handoff. |
| 6 | Sprint 107 | Runtime configuration and secret posture review | Production deployments need explicit failure behavior when required auth secrets are missing. | Startup/runtime checks fail closed for missing production auth settings. Operator docs describe required secrets, rotation expectations, and dev-only exceptions. |
| 7 | Sprint 108 | Observability and audit event quality | Postgres has events and jobs, but production operations need consistent correlation and safe diagnostics. | Lifecycle events, job events, artifact refs, ServiceNow work notes, and admin views share correlation ids. Error messages are redacted and actionable. |
| 8 | Sprint 109 | Rate limiting and abuse controls | Public API exposure needs request volume controls even when authenticated. | Lifecycle and admin endpoints have bounded request sizes, bounded list limits, and documented rate/abuse behavior. |
| 9 | Sprint 110 | Capability backlog design | Generic dictionary/form placement is the only baseline build capability. The next capability should be selected deliberately. | ADR names the next supported capability, required validators, unsupported cases, and UAT story shape before implementation begins. |

## Review Gates

### Slop review

Run after the hardening backlog closes enough to claim production readiness.

Review for:

- Overgrown modules that should be split.
- Duplicated logic between CLI, runtime, and ServiceNow clients.
- Vague names that hide security or lifecycle meaning.
- Dead code from pre-MVP paths that creates confusion.
- Tests that assert implementation details instead of behavior.
- Docs that still describe earlier MVP assumptions as current behavior.
- Any "temporary" mechanism that is now on the production path.

### Security review

Run after Sprint 102 and Sprint 103 at minimum.

Review for:

- Unauthenticated public endpoints.
- Admin console authentication and authorization gaps.
- Webhook replay, spoofing, and request tampering.
- Secrets in logs, artifacts, prompts, errors, tests, and docs.
- Over-broad ServiceNow credentials or Table API privileges.
- Unsafe ServiceNow mutation paths that bypass retrieved Update Set review.
- Model/provider calls without policy, data minimization, or audit metadata.
- Artifact payloads containing ServiceNow sys_ids or unnecessary sensitive data.
- Missing operational controls for rate limiting, request size, and failure alerting.

## Immediate Execution Order

1. Sprint 102: Admin auth strategy boundary.
2. Sprint 103: Authenticated inbound lifecycle webhook.
3. Sprint 104: Confidence-based context retrieval worker.
4. Sprint 105: Admin console drill-down and evidence views.
5. Sprint 106: ATO evidence refresh.
6. Sprint 107: Runtime configuration and secret posture review.

The later slop/security review should not wait for every future feature. It should run once the authentication boundary, webhook boundary, and context retrieval boundary are hardened enough that findings are about production quality rather than known MVP gaps.
