# Sprint 144 Change Log

## Structured UI Policy gate hardening

- Live UAT of `STRY0010024` showed the gate treating structured negative boundaries as requested behavior.
- `Run scripts: false` is now allowed for UI Policy generation; only enabled run scripts or advanced scripts remain forbidden.
- Negative safety constraints such as `Do not use Client Script, Business Rule, Script Include, Flow, ACL, integration calls, credentials, or cross-table behavior` are now filtered through shared requirement-text parsing before capability detection.
- Surface context discovery uses the same positive requirement text, so forbidden `Flow` wording no longer requests `flows` or `flow_graph` context for a declarative UI Policy story.
- The structured `STRY0010024` story shape now gates to the supported `ui_policy_generate` path with required context limited to `table_schema`, `form_layout`, and `ui_policies`.
