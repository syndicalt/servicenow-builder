# Sprint 141 Change Log

## Supported artifact UAT parser hardening

- Live UAT exposed that negative safety instructions such as "Do not create ACLs, flows, data migration, or integrations" were being treated as requested capabilities.
- Capability analysis now strips negated clauses before deciding which automation capabilities are requested, while retaining the full story text for field and implementation metadata extraction.
- This keeps safety constraints from becoming false blockers and preserves fail-closed routing for positively requested unsupported capabilities.

## ServiceNow model output normalizers

- Business Rule generation now accepts common model aliases for operation flags: `insert`, `update`, `operation_insert`, and `operation_update`.
- Business Rule generation also accepts action text such as `insert or update` and plural `conditions` when models emit those instead of explicit operation booleans and `filter_condition`.
- Business Rule generation continues to accept `action_script` and `script_body` as script aliases and infers `fields_written` from direct `current.<field>` writes when the model omits that metadata.
- Script Include generation infers public methods from the generated prototype when the model omits `public_methods`.
- Script Include stories that mention fields read or use words containing "form" are no longer misclassified as dictionary/form stories.

## Live UAT impact

- These fixes were driven by the supported-artifact UAT matrix for dictionary/form, Business Rule, Client Script, Script Include, and UI Policy stories.
- The current mutation boundary remains retrieved Update Set handoff for supported generated artifacts; unsupported or insufficient-context requests continue to route to human review.

## Bootstrap field writability correction

- Live UAT proved dictionary `read_only=true` prevents the worker from persisting `u_ai_status` and retrieved Update Set handoff metadata through the Table API.
- Bootstrap now creates AI operational fields with dictionary `read_only=false` and remediates existing read-only AI operational fields back to writable.
- Human read-only behavior must be enforced outside the dictionary flag with form policy, UI policy, ACLs, or role-scoped controls that still allow the integration identity to write.
