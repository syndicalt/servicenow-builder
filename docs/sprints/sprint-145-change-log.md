# Sprint 145 Change Log

## Typed intent architecture

- Live UAT of `STRY0010022` showed the raw-text gate architecture was too brittle: newline-delimited structured story fields were parsed as one large clause, and `cmdb_ci` field reads could request `cmdb_discovery_maps`.
- Added `AutomationIntent` as the production boundary between story text and deterministic validation.
- `extract_automation_intent()` now parses structured story key/value fields such as `Target artifact type:`, `Target table:`, `Fields read:`, `Fields written / affected:`, and `Forbidden behavior:`.
- Capability analysis now prefers typed structured intent and uses legacy raw-text heuristics only when no structured intent exists.
- Implementation packets now include typed intent in `normalized_intent`, so the model receives normalized fields, required context, and safety boundaries instead of relying only on prose.
- Shared requirement-text parsing still treats line breaks as requirement boundaries, so a later `Forbidden behavior:` line does not remove earlier `Fields read:` or `Fields written / affected:` details.
- Surface context discovery uses regex-based fallback matching, and the typed intent path supplies explicit required context. Ordinary Client Script field reads stay scoped to `table_schema` and `client_scripts`; explicit CMDB or discovery-map requests still retrieve CMDB/discovery context.
