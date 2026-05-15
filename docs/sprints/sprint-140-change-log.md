# Sprint 140 Change Log

## Sys_id-backed lifecycle lookup

- Live supported-artifact UAT found duplicate `rm_story.number` values in the PDI.
- The lifecycle event contract now accepts `story_sys_id` from the ServiceNow Business Rule.
- Workers use `story_sys_id` as the authoritative ServiceNow lookup key when it is present and fall back to `story_number` only for legacy events.
- Failure writeback also fetches by `story_sys_id` before writing `Automation Failed` notes or moving the story back to Draft.
- Admin API and console summaries continue to omit `story_sys_id`; story number remains the human-readable correlation value.

## Bootstrap impact

- The lifecycle Business Rule bootstrap now emits `story_sys_id: current.getUniqueValue()`.
- Existing installed lifecycle webhook records must be reapplied before live UAT can be trusted, because old Business Rules emit number-only events.
