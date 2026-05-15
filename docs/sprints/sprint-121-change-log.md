# Sprint 121 Change Log

## Goal

Harden the executable ServiceNow generation validators before expanding the supported build surface.
This is a generation validator hardening sprint, not a new capability sprint.

## Changes

- Added focused generation validator coverage for Business Rule, Client Script, and Script Include handoff paths.
- Closed a Business Rule validation gap by treating `current.setValue(...)` and bracket writes as declared field writes.
- Closed a Client Script validation gap by treating `g_form.clearValue(...)` as a declared field write.
- Tightened the first Script Include generation subset to global-only Script Include output until scoped XML generation can retrieve and emit the correct scope metadata.
- Required generated Script Include candidates to declare at least one public method.
- Rejected generated Script Include candidates that declare table or field writes in the current utility-only profile.

## Boundary

This sprint does not add a new ServiceNow artifact surface. It reduces production risk in the existing generation surfaces and preserves the current 3 story point automation limit while the target maturity remains 5 story points.

## Tests

- Added validator tests proving unsafe or inconsistent generation candidates fail closed before retrieved Update Set import.
- Kept the project-level 90% coverage gate as the release boundary.
