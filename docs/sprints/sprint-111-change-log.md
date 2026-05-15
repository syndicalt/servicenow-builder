# Sprint 111 Change Log

## Goal

Capability backlog design: define the capability expansion path before adding another ServiceNow mutation surface.

## Changes

- Added ADR 0006 for the capability extension architecture.
- Defined a versioned `CapabilityProfile` contract and capability registry.
- Documented required context surfaces through `required_instance_context`.
- Documented deterministic validators, unsupported cases, UAT story shape, and retrieved Update Set handoff expectations.
- Selected Business Rule analysis first for Sprint 112 as a context-only first implementation.
- Documented Business Rule generation as the next mutation candidate after the analysis profile and validators are proven.
- Flow Designer remains context-only; Flow Designer context-only work can proceed only as review and investigation until its graph shape and validators are separately profiled.
- Updated the production hardening backlog and operator guide.

## Decision

No new mutation surface was added in Sprint 111. The sprint deliberately constrains future work so that new capabilities must be introduced through a profile, sufficient live instance context, deterministic validators, tests, and ServiceNow-native retrieved Update Set review.

For test and release tracking: no new mutation surface.

## Tests

- Added documentation tests for ADR 0006.
- Added operator guide tests for the Capability Extension Model.
- Added backlog tests to keep Sprint 112 aligned to Business Rule analysis first.
