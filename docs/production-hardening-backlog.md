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
| 20 | Sprint 121 | Generation validator hardening | Executable ServiceNow artifact generation must fail closed on common write and scope mismatches before another mutation surface is added. | Business Rule, Client Script, and Script Include validators cover additional unsafe write/scope cases, and coverage remains above the 90% gate. |
| 21 | Sprint 122 | UI Policy generation profile design | UI Policies are the next lower-risk ServiceNow surface, but they need an explicit declarative boundary before mutation is enabled. | ADR 0010 defines `ui_policy_generate`, supported subset, forbidden cases, output schema, deterministic validators, Update Set XML shape, UAT story shape, and confirms No runtime generation is enabled. |
| 22 | Sprint 123 | UI Policy generation implementation | The profile is designed; implementation can add reviewed declarative form behavior without using Client Script as a workaround. | Implement `ui_policy_generate` behind deterministic validators, generate reviewed `sys_ui_policy` and `sys_ui_policy_action` / `sys_update_xml` retrieved Update Set handoff, and keep forbidden cases routed to human review. |
| 23 | Sprint 124 | Flow Designer generation profile design | Flow Designer is graph-oriented and cannot safely be treated as a single-record generator. | ADR 0011 defines `flow_modify`, supported subset, forbidden cases, graph output schema, deterministic validators, Update Set XML evidence requirements, UAT story shape, and confirms No runtime generation is enabled. |
| 24 | Sprint 125 | Flow graph retrieval hardening | Flow mutation must not begin until the app can retrieve and validate a complete current flow graph. | Flow context includes retrieved trigger, action, logic, input, and output records with citations, excludes runtime history tables, and fails closed when the graph is incomplete. |
| 25 | Sprint 126 | Flow graph diff contract validation | Flow mutation needs a structured model output contract before any builder can create customer updates. | Add validation-only `sys_hub_flow_graph_diff` support for narrow `add_action` and `update_condition` diffs, reject raw XML and unretrieved node references, and keep retrieved Update Set handoff disabled for Flow Designer. |
| 26 | Sprint 127 | Flow builder preflight design | A future Flow builder must prove graph freshness and required XML-shape evidence before creating customer updates. | Add design-only builder preflight planning, verify retrieved graph hash, reject premature customer updates, keep runtime generation disabled, and keep retrieved Update Set handoff disabled. |
| 27 | Sprint 128 | Flow XML shape repository | A future Flow builder needs explicit reviewed XML shape metadata before it can emit customer updates. | Add `flow-xml-shapes-v1` metadata for `sys_hub_flow`, `sys_hub_action_instance`, and `sys_hub_flow_logic_instance_v2`, connect it to builder preflight, and keep Flow XML generation disabled. |
| 28 | Sprint 129 | Flow XML shape evidence validation | A future Flow builder needs to prove retrieved XML review samples match the repository contract before customer updates can be emitted. | Add validation-only Flow XML evidence checks for root, action, required fields, and forbidden fields; expose `xml_shape_evidence_validator_available`; keep Flow XML generation and retrieved Update Set handoff disabled. |
| 29 | Sprint 130 | Flow customer update strategy | Flow mutation needs deterministic update names and rollback strategy before any customer update builder exists. | Add `flow-customer-update-strategy-v1`, define `table_sys_id` naming, reject unsupported Flow tables and unstable sys_ids, define rollback strategy coverage for `add_action` and `update_condition`, and keep Flow XML generation disabled. |
| 30 | Sprint 131 | Flow snapshot update strategy | Flow mutation needs explicit snapshot evidence rules before any customer update builder can touch `sys_hub_flow.latest_snapshot`. | Add `flow-snapshot-update-strategy-v1`, require retrieved `latest_snapshot` evidence, reject unstable snapshot references, reject snapshot table mutation, and keep Flow XML generation disabled. |
| 31 | Sprint 132 | Flow preview/commit review strategy | Flow mutation needs an explicit human review boundary before retrieved Update Set handoff can ever be enabled. | Add `flow-preview-commit-review-strategy-v1`, require preview before commit, require human commit, reject auto-commit, and keep Flow XML generation and retrieved Update Set handoff disabled. |
| 32 | Sprint 133 | Flow builder readiness contract | Flow mutation needs one auditable readiness object before any future builder is considered. | Add `flow-builder-readiness-v1`, aggregate required evidence, report `missing_evidence`, keep runtime generation and retrieved Update Set handoff disabled, and keep blocked reason `Flow Designer builder is not implemented`. |
| 33 | Sprint 134 | Flow builder plan readiness wiring | Flow preflight consumers should not be able to ignore the readiness contract. | Add readiness contract version, missing evidence, disabled readiness flags, and blocked reason to Flow builder preflight plans; keep Flow XML generation and retrieved Update Set handoff disabled. |
| 34 | Sprint 135 | Flow unsupported reason codes | Flow orchestration should not parse human blocker text to route unsupported work. | Add `unsupported_reason_codes` to the readiness contract and builder preflight plan; include `flow_builder_not_implemented`, `runtime_generation_disabled`, and `retrieved_update_set_handoff_disabled`; keep Flow XML generation and handoff disabled. |
| 35 | Sprint 136 | Flow unsupported reason guidance | Operators need stable next-step guidance for unsupported Flow work without duplicating prose across worker and admin surfaces. | Add `unsupported_reason_guidance` with stable summaries, `route_to_human_review`, and ServiceNow work note text for every unsupported reason code; keep Flow XML generation and handoff disabled. |
| 36 | Sprint 137 | Flow preflight guidance artifact | Flow guidance should be available in persisted fulfillment evidence, not only validator module metadata. | Add a `flow_preflight_guidance` artifact with schema `flow-preflight-guidance-v1`, disabled readiness flags, unsupported reason codes, and `route_to_human_review` guidance whenever runtime sees `flow_modify`; keep Flow XML generation and handoff disabled. |
| 37 | Sprint 138 | Flow preflight guidance work note | ServiceNow users need actionable Flow routing feedback without opening the DB artifact store first. | Include the `flow_preflight_guidance` artifact reference and readiness-contract work-note guidance in manual-review ServiceNow work notes for unsupported `flow_modify`; keep Flow XML generation and handoff disabled. |
| 38 | Sprint 139 | Supported artifact UAT hardening | Live testing all supported ServiceNow artifact types exposed context payload and Script Include context defects before the matrix could complete. | Compact model payloads to required surfaces, avoid duplicate instance context in model calls, and allow Script Include-only context without table/form layout requirements before rerunning the live UAT matrix. |

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
20. Sprint 121: Generation validator hardening.
21. Sprint 122: UI Policy generation profile design.
22. Sprint 123: UI Policy generation implementation.
23. Sprint 124: Flow Designer generation profile design.
24. Sprint 125: Flow graph retrieval hardening.
25. Sprint 126: Flow graph diff contract validation.
26. Sprint 127: Flow builder preflight design.
27. Sprint 128: Flow XML shape repository.
28. Sprint 129: Flow XML shape evidence validation.
29. Sprint 130: Flow customer update strategy.
30. Sprint 131: Flow snapshot update strategy.
31. Sprint 132: Flow preview/commit review strategy.
32. Sprint 133: Flow builder readiness contract.
33. Sprint 134: Flow builder plan readiness wiring.
34. Sprint 135: Flow unsupported reason codes.
35. Sprint 136: Flow unsupported reason guidance.
36. Sprint 137: Flow preflight guidance artifact.
37. Sprint 138: Flow preflight guidance work note.
38. Sprint 139: Supported artifact UAT hardening.
39. Sprint 140: Sys_id-backed lifecycle lookup.
40. Sprint 141: Supported artifact UAT parser hardening.
41. Sprint 142: Business Rule gate inference hardening.
42. Sprint 143: Business Rule script metadata separation.
43. Sprint 144: Structured UI Policy gate hardening.
44. Sprint 145: Typed intent architecture.
45. Sprint 146: Dictionary/form typed intent alias hardening.
46. Sprint 147: Script Include structured story hardening.

The later slop/security review should not wait for every future feature. It should run once the authentication boundary, webhook boundary, and context retrieval boundary are hardened enough that findings are about production quality rather than known MVP gaps.
