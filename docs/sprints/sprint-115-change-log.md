# Sprint 115 Change Log

## Goal

Add the generation foundation and maturity model that lets the product target autonomous handling of 5 story points without enabling unsafe mutation surfaces prematurely.

## Changes

- Added `current_max_story_points` and `target_max_story_points` to `CapabilityProfile`.
- Set the full-maturity autonomous target to 5 story points.
- Separated the current 3 story point automation ceiling from the 5 story point full-maturity target.
- Added `researcher` and `build_pipeline` metadata to each capability profile.
- Added generation profiles for handled surfaces:
  - `business_rule_generate`
  - `client_script_generate`
  - `script_include_generate`
- Kept `business_rule_generate` designed but not enabled at runtime.
- Kept `client_script_generate` and `script_include_generate` planned but not enabled at runtime.
- Kept dictionary/form generation enabled with a 3 story point current limit and a 5 story point maturity target.

## Decision

Sprint 115 is the foundation for autonomous generation rules, researchers, and build pipelines across handled surfaces. It does not enable new code-surface mutation. Runtime generation for Business Rules moves to Sprint 116 and must use the `business_rule_generate` profile, deterministic validators, and reviewed retrieved Update Set handoff.

## Tests

- Added capability profile tests for current and target maturity.
- Added generation registry tests for handled surfaces.
- Added analyzer tests proving work above the current 3 story point limit routes to manual build while the maturity target remains 5.
- Added operator-guide and backlog documentation tests.
