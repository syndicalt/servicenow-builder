# Typed Intent Architecture Design

## Problem

The current automation gate uses raw story text to infer requested capabilities, required ServiceNow context, and missing details. That made negative constraints and field names look like requested work: `Do not use Flow` could request Flow context, `cmdb_ci` could request CMDB/discovery context, and newline formatting could hide `Fields read` / `Fields written` details.

## Decision

Rebuild the production gate around a typed intent boundary.

1. Extract a typed `AutomationIntent` from the story before capability analysis.
2. Validate the typed intent deterministically.
3. Derive capability, target table, required context, and missing details from the typed intent.
4. Keep deterministic validators as the final safety boundary for generated candidates and Update Set handoff.

The MVP extractor is a strict structured-story extractor. It parses explicit key/value lines such as `Target artifact type:`, `Target table:`, `Fields read:`, and `Forbidden behavior:`. It does not try to semantically classify arbitrary prose as production intent. Legacy prose heuristics remain as fallback while existing tests and older stories are migrated.

## Supported Typed Intents

- Dictionary/form field intent.
- Business Rule generation intent.
- Client Script generation intent.
- Script Include generation intent.
- UI Policy generation intent.

Flow Designer, ACL, integration, and data migration stories remain unsupported or manual-review unless a future typed intent and validator profile is implemented.

## Data Flow

1. ServiceNow story arrives.
2. `extract_automation_intent(story)` creates a typed intent when structured fields are present.
3. `analyze_story_capabilities(story)` validates that intent and returns `StoryCapabilityAssessment`.
4. Required context surfaces come from the capability profile named by the typed intent.
5. `discover_servicenow_surface_context()` receives explicit required surfaces from the assessment.
6. `build_implementation_packet()` includes the typed intent in `normalized_intent`.
7. The model builds a candidate from the typed intent plus retrieved context.
8. Surface-specific deterministic validators approve or reject the candidate before retrieved Update Set creation.

## Safety Rules

- Negative boundaries in `Forbidden behavior:` never create requested capabilities.
- Field names such as `cmdb_ci` never imply CMDB/discovery-map work by themselves.
- Disabled behavior such as `Run scripts: false` is not forbidden.
- Missing required typed fields routes to Needs Clarification.
- Unsupported artifact types route to unsupported/manual review.
- Generated artifacts still must pass existing deterministic validators.

## Testing

Tests must prove:

- Structured `STRY0010022` extracts a Client Script intent with `category` and `cmdb_ci` as fields read, no fields written, and required context limited to table schema and client scripts.
- Structured `STRY0010024` extracts a UI Policy intent and ignores forbidden Client Script / Flow / ACL wording as requested work.
- Implementation packets include the typed intent in `normalized_intent`.
- Context discovery does not request `cmdb_discovery_maps` for ordinary `cmdb_ci` field reads.
- Existing capability and generation tests remain above the 90% coverage gate.
