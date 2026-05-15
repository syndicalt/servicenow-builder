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
| 4 | Sprint 105 | HMAC PDI/Railway cutover | The PDI and hosted API needed to prove the signed lifecycle emitter path, not just local request validation. | Unsigned lifecycle calls are rejected, signed ServiceNow `sha256-base64` calls are accepted, and the signing secret is kept out of artifacts and docs. |
| 5 | Sprint 106 | ServiceNow surface investigation | Generic table/form context is not enough for model implementation planning across ServiceNow surfaces. | The worker retrieves table schema, form layout, Business Rules, Client Scripts, UI Policies, Flow records, Script Includes, ACL indicators, CMDB/discovery, integrations, and curated public-doc query context before provider calls. |
| 6 | Sprint 107 | Surface evidence hardening | Retrieved context needs provenance and minimization before it is safe to show in admin views or send to models. | Surface contexts include confidence scores and citations, script-like fields are redacted, endpoint query strings are redacted, and missing context is named in ServiceNow work notes. |
| 7 | Sprint 108 | Runtime configuration and secret posture review | Production deployments need explicit failure behavior when required auth secrets are missing. | Startup/runtime checks fail closed for missing production auth settings. Operator docs describe required secrets, rotation expectations, and dev-only exceptions. |
| 8 | Sprint 109 | Observability and audit event quality | Postgres has events and jobs, but production operations need consistent correlation and safe diagnostics. | Lifecycle events, job events, artifact refs, ServiceNow work notes, and admin views share correlation ids. Error messages are redacted and actionable. |
| 9 | Sprint 110 | Rate limiting and abuse controls | Public API exposure needs request volume controls even when authenticated. | Lifecycle and admin endpoints have bounded request sizes, bounded list limits, and documented rate/abuse behavior. |
| 10 | Sprint 111 | Capability backlog design | Generic dictionary/form placement is the only baseline build capability. The next capability should be selected deliberately. | ADR names the extension contract; ADR 0006 names the extension contract, `CapabilityProfile` requirements, required validators, unsupported cases, UAT story shape, and Business Rule analysis first before implementation begins. |
| 11 | Sprint 112 | Business Rule analysis capability | Business Rules are the right next capability candidate, but generation should not start until the app can retrieve and classify the live `sys_script` surface. | Done: context-only first implementation retrieves relevant Business Rule context, classifies candidate stories, names missing inputs and unsupported cases, stores code surface analysis evidence, and adds no new mutation surface. |
| 12 | Sprint 113 | Code surface analysis capability | Business Rule, Client Script, and Script Include analysis share the same code-surface pattern; duplicating one-off analyzers would create drift before generation profiles exist. | Done: `business_rule_analyze`, `client_script_analyze`, and `script_include_analyze` use shared `code-surface-analysis-v1` artifacts, skip model calls, skip retrieved Update Set creation, and write human-review feedback. |
| 13 | Sprint 114 | Business Rule generation profile design | Business Rule generation should not be implemented until the mutation profile, validators, XML evidence, and UAT story shape are explicit. | ADR 0007 defines `business_rule_generate`, supported subset, forbidden cases, output schema, deterministic validators, Update Set XML shape, UAT story shape, and confirms No runtime generation is enabled. |
| 14 | Sprint 115 | Generation foundation and maturity model | The product target is autonomous handling of 5 story point work, but each surface needs explicit maturity, researcher, and build pipeline metadata before mutation expands. | `CapabilityProfile` records `current_max_story_points`, `target_max_story_points`, `researcher`, and `build_pipeline`; handled surfaces have generation profiles; analysis uses a 5 story point full-maturity ceiling. |
| 15 | Sprint 116 | Business Rule generation implementation | The profile and maturity foundation are now designed; implementation can begin without inventing the mutation boundary during coding. | Implement `business_rule_generate` behind deterministic validators, generate reviewed `sys_script` / `sys_update_xml` retrieved Update Set handoff, and keep forbidden cases routed to human review. |
| 16 | Sprint 117 | Client Script generation profile design | Client Scripts are the next code-surface candidate, but browser-side behavior needs a separate safety case before mutation is enabled. | ADR 0008 defines `client_script_generate`, supported subset, forbidden cases, output schema, deterministic validators, Update Set XML shape, UAT story shape, and confirms No runtime generation is enabled. |
| 17 | Sprint 118 | Client Script generation implementation | The profile is designed; implementation can follow the Business Rule pattern without inventing client-side validators during coding. | Implement `client_script_generate` behind deterministic validators, generate reviewed `sys_script_client` / `sys_update_xml` retrieved Update Set handoff, and keep forbidden cases routed to human review. |
| 18 | Sprint 119 | Script Include generation profile design | Script Includes are reusable server-side code and need a separate safety case before mutation is enabled. | ADR 0009 defines `script_include_generate`, supported subset, forbidden cases, output schema, deterministic validators, Update Set XML shape, UAT story shape, and confirms No runtime generation is enabled. |
| 19 | Sprint 120 | Script Include generation implementation | The profile is designed; implementation can follow a narrow utility-only boundary without coupling caller generation to the same candidate. | Implement `script_include_generate` behind deterministic validators, generate reviewed `sys_script_include` / `sys_update_xml` retrieved Update Set handoff, and keep forbidden cases routed to human review. |

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
4. Sprint 105: HMAC PDI/Railway cutover.
5. Sprint 106: ServiceNow surface investigation.
6. Sprint 107: Surface evidence hardening.
7. Sprint 108: Runtime configuration and secret posture review.
8. Sprint 109: Observability and audit event quality.
9. Sprint 110: Rate limiting and abuse controls.
10. Sprint 111: Capability backlog design.
11. Sprint 112: Business Rule analysis capability.
12. Sprint 113: Code surface analysis capability.
13. Sprint 114: Business Rule generation profile design.
14. Sprint 115: Generation foundation and maturity model.
15. Sprint 116: Business Rule generation implementation.
16. Sprint 117: Client Script generation profile design.
17. Sprint 118: Client Script generation implementation.
18. Sprint 119: Script Include generation profile design.
19. Sprint 120: Script Include generation implementation.

The later slop/security review should not wait for every future feature. It should run once the authentication boundary, webhook boundary, and context retrieval boundary are hardened enough that findings are about production quality rather than known MVP gaps.
