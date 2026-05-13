# ADR 0001: Test-First and No-Hacks Engineering Policy

## Status

Accepted.

## Context

This project targets regulated Federal ServiceNow delivery workflows. Hidden shortcuts, weak abstractions, and test-after development create unacceptable audit, safety, and maintenance risk.

## Decision

All behavior changes must start with a failing test. The project enforces a 90% coverage gate, but coverage is not treated as a substitute for meaningful assertions. Temporary hacks, bypasses, and undocumented compliance exceptions are prohibited. When the design is wrong, the engineering path is to rework the design.

## Consequences

- Sprints may take longer early in the project.
- Tests become the executable record of expected behavior.
- Reviewers can reject changes that pass tests but rely on hidden shortcuts or weak abstractions.
- Compliance-sensitive behavior must fail closed and be directly tested.
