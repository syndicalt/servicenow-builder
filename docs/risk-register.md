# Risk Register

| Risk | Status | Mitigation |
|---|---|---|
| PDI OAuth configuration differs from Federal production OAuth setup | Open | Keep auth behind an adapter and document PDI-only assumptions |
| Story type classifier is intentionally narrow | Accepted | Route unknown work to manual review |
| Template-only generation may produce low automation rate | Accepted | Measure approval/rejection reasons before adding model calls |
| No approved model provider selected | Open | Rules-only mode remains default; Sprint 163 added an Anthropic Messages API adapter at OpenAI parity as a second-provider option, but it is not wired into runtime provider selection and policy approval is still required |
| XML export not implemented | Accepted | JSON candidate review must prove quality first |
| Live tests depend on PDI availability | Mitigated | Default test suite uses fake transports only |
