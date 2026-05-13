# Sprint 55 Change Log

## Update Set XML Marker Gate

- Tightened `review-delivery-artifact` for Update Set XML review.
- Required reviewed Update Set XML to contain a `sys_update_xml` entry before creating a `reviewed_export` job.
- Kept smoke placeholder XML blocked.
- Made empty unload XML fail closed with `reason=reviewed_export_artifact_required`.
- Updated reviewed artifact tests and operator documentation to use a real Update Set XML marker.
