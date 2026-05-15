# Sprint 105 Change Log

## Goal

Cut over the development Railway and ServiceNow PDI lifecycle webhook path from unauthenticated delivery to HMAC-signed delivery.

## Changes

- Generated a reviewed signed lifecycle webhook bootstrap artifact:
  - `artifacts/lifecycle-bootstrap/lifecycle-business-rule-sprint-105-20260515.json`
- Created or updated the ServiceNow system property:
  - `x_jedi.lifecycle.webhook.secret`
- Applied the signed lifecycle webhook bootstrap records to ServiceNow:
  - `sys_rest_message`
  - `sys_rest_message_fn`
  - `sys_script`
- Wrote apply audit evidence:
  - `artifacts/bootstrap-audit/lifecycle-webhook-apply-sprint-105-20260515.json`
- Verified the installed ServiceNow records:
  - `artifacts/bootstrap-verification/lifecycle-webhook-verify-sprint-105-20260515.json`
- Set Railway lifecycle webhook runtime variables for the API and worker:
  - `JEDI_LIFECYCLE_WEBHOOK_SECRET`
  - `JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE=hmac_sha256`
  - `JEDI_LIFECYCLE_WEBHOOK_MAX_SKEW_SECONDS=300`

## Verification

- ServiceNow lifecycle webhook verification reported:
  - `lifecycle_webhook_verified=True`
  - `matched_records=3`
  - `missing_records=0`
- Railway API deployment after auth flip:
  - `ccf08ca8-83a6-4c6f-8645-09f2d57793f7`
  - `SUCCESS`
- Railway worker deployment after auth variable update:
  - `44bcdefd-f822-4568-a008-01b32bc8557b`
  - `SUCCESS`
- Public API smoke checks:
  - `GET /health` returned `{"status":"ok"}`
  - unsigned `POST /lifecycle/events` returned `401`
  - signed `sha256-base64` `POST /lifecycle/events` returned `202`

## Decision

The PDI now exercises the same authenticated webhook boundary intended for production-shaped deployments. The signing secret is stored only in runtime configuration and the ServiceNow system property; it is not recorded in the bootstrap artifact, audit artifact, git history, or sprint documentation.
