# Sprint 104 Change Log

## Goal

Make the ServiceNow lifecycle webhook bootstrap capable of emitting the authenticated HMAC requests accepted by the API boundary from Sprint 103.

## Changes

- Added `sha256-base64=<mac>` support to the lifecycle receiver for ServiceNow emitters.
- Kept existing `sha256=<hex hmac>` support for generic clients.
- Added `--hmac-secret-property-name` to `plan-lifecycle-business-rule`.
- Extended the generated Business Rule so it can:
  - Read the webhook signing secret from a ServiceNow system property.
  - Sign `<timestamp>.<body>` using `GlideCertificateEncryption.generateMac()`.
  - Send `X-JEDI-Webhook-Timestamp`.
  - Send `X-JEDI-Webhook-Signature: sha256-base64=<mac>`.
- Kept the secret value out of the bootstrap artifact and generated script.
- Updated the operator guide for the ServiceNow property and matching API runtime secret.

## Tests

- Added API coverage for ServiceNow-style Base64 HMAC signatures.
- Added bootstrap coverage for the HMAC Business Rule script shape.
- Added CLI coverage for `--hmac-secret-property-name`.
- Added docs coverage for the Base64 HMAC behavior.

## Decision

ServiceNow's supported server-side MAC API returns Base64 output, so the API now accepts an explicit `sha256-base64=` signature scheme instead of forcing unsupported or brittle hex conversion inside the Business Rule. This keeps the emitter small, reviewable, and based on documented ServiceNow primitives while preserving the existing hex signature path for non-ServiceNow clients.
