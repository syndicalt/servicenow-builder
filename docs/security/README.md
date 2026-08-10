# Security Documentation

Security and compliance documentation for the JEDI DevProject sidecar runtime. The canonical
architecture, components, and trust-boundary diagrams live in
[`../system-architecture.md`](../system-architecture.md); this directory holds the
security-focused analysis.

## Documents

| Document | Purpose |
|---|---|
| [threat-model.md](threat-model.md) | Assets, trust boundaries, enumerated threats, and the implemented control that mitigates each one, with code evidence. |
| [data-flow.md](data-flow.md) | Security-focused data flow: where regulated data moves, the control at each crossing, redaction points, and prohibited flows. |
| [control-mapping.md](control-mapping.md) | Mapping of implemented controls to code, configuration, and test evidence; deployment-held controls and open control work. |

Related documents outside this directory:

- [`../policies/local-regulated-data.md`](../policies/local-regulated-data.md) — data-handling
  rules for local development and fixtures.
- [`../admin-auth-config.md`](../admin-auth-config.md) — admin console and JSON API
  authentication modes, token rules, and the reserved OIDC/ServiceNow OAuth paths.
- [`../operator-guide.md`](../operator-guide.md) — operational detail: "Lifecycle Webhook
  Authentication", "Rate Limits and Payload Bounds", "Production Runtime Fail-Closed Checklist",
  and "Secret Inventory".

## Reading Order

1. Start with `../system-architecture.md` for components and trust boundaries.
2. Read [threat-model.md](threat-model.md) for what can go wrong and what stops it.
3. Read [data-flow.md](data-flow.md) for where data moves and where redaction applies.
4. Use [control-mapping.md](control-mapping.md) when assembling compliance evidence.

## Posture Summary

The system is dry-run and fail-closed by default: webhook authentication, admin authentication,
model provider selection, alert egress, public web access, and ServiceNow mutation all require
explicit configuration, and production startup validation rejects missing or malformed security
settings before the runtime serves traffic. This documentation is engineering evidence for a
customer ATO package; it is not itself an authorization.
