# Sprint 127 Change Log

## Flow builder preflight design

Sprint 127 added an executable Flow Designer builder preflight plan. The runtime generation remains disabled.

Changes:

- Added `plan_flow_graph_builder` for validation-only builder planning.
- Verified `retrieved_graph_hash_matches_existing_graph_hash` before any future builder can proceed.
- Required empty `customer_update_records` because generated Flow customer updates are not supported yet.
- Kept `runtime_generation_enabled=false`.
- Kept retrieved Update Set handoff disabled; retrieved Update Set handoff remains disabled.
- Reported the explicit blocked reason: `Flow Designer builder is design-only`.
- Defined required builder evidence: `xml_shape_repository_available`, customer update naming, flow snapshot update strategy, rollback customer update strategy, and ServiceNow preview/commit review.

Boundary:

This sprint does not create `sys_update_xml`, does not import a retrieved Update Set, and does not mutate Flow Designer records. It gives the future builder a production preflight contract so implementation cannot skip graph hash verification or missing XML-shape evidence.

Verification:

- Added failing tests first for builder preflight planning.
- Added stale graph hash rejection.
- Added rejection for premature customer update records.
- Preserved the 90 percent coverage gate.
