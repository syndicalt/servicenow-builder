"""Runtime FastAPI app factory: lifecycle API plus admin artifact and console routes."""

from __future__ import annotations

import html
import json
from datetime import datetime
from typing import Any

from fastapi import FastAPI, Header, HTTPException, status
from fastapi.responses import HTMLResponse

from jedi_devproject.lifecycle_api import create_lifecycle_api
from jedi_devproject.operational_store import (
    ArtifactBlobRecord,
    ArtifactRefRecord,
    FulfillmentJobRecord,
    LifecycleEventRecord,
)
from jedi_devproject.rate_limit import InMemoryRateLimiter
from jedi_devproject.runtime_auth import (
    _require_admin_console_credentials,
    _require_admin_rate_limit,
    _require_admin_token,
)
from jedi_devproject.runtime_config import RuntimeSettings, validate_runtime_settings
from jedi_devproject.runtime_redaction import _redact_diagnostic_text
from jedi_devproject.runtime_servicenow import (
    _servicenow_complete_notifier,
    _servicenow_story_client_from_settings,
)
from jedi_devproject.runtime_store import DEFAULT_STORE_FACTORY, StoreFactory
from jedi_devproject.servicenow import HttpTransport, UrllibTransport


def create_runtime_api(
    *,
    settings: RuntimeSettings,
    store_factory: StoreFactory = DEFAULT_STORE_FACTORY,
    transport: HttpTransport | None = None,
    lifecycle_rate_limiter: InMemoryRateLimiter | None = None,
    admin_rate_limiter: InMemoryRateLimiter | None = None,
) -> FastAPI:
    validate_runtime_settings(settings)
    lifecycle_limiter = lifecycle_rate_limiter or _rate_limiter(
        max_requests=settings.lifecycle_rate_limit_max_requests,
        window_seconds=settings.lifecycle_rate_limit_window_seconds,
    )
    admin_limiter = admin_rate_limiter or _rate_limiter(
        max_requests=settings.admin_rate_limit_max_requests,
        window_seconds=settings.admin_rate_limit_window_seconds,
    )
    store = store_factory(settings.database_url)
    request_transport = transport or UrllibTransport()
    story_client = _servicenow_story_client_from_settings(
        settings=settings,
        transport=request_transport,
    )
    app = create_lifecycle_api(
        store=store,
        complete_notifier=_servicenow_complete_notifier(client=story_client),
        webhook_auth_mode=settings.lifecycle_webhook_auth_mode,
        webhook_secret=settings.lifecycle_webhook_secret,
        runtime_environment=settings.runtime_environment,
        webhook_max_skew_seconds=settings.lifecycle_webhook_max_skew_seconds,
        max_request_body_bytes=settings.lifecycle_webhook_max_body_bytes,
        rate_limiter=lifecycle_limiter,
    )

    @app.get("/artifacts/{artifact_id}")
    def get_artifact(
        artifact_id: int,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _require_admin_rate_limit(admin_rate_limiter=admin_limiter, key="artifacts")
        _require_admin_token(settings=settings, authorization=authorization)
        try:
            artifact = store.get_artifact_blob(artifact_id)
        except KeyError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="artifact not found",
            ) from exc
        return _artifact_blob_response(artifact)

    @app.get("/jobs/{job_id}/artifacts")
    def list_job_artifacts(
        job_id: str,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _require_admin_rate_limit(admin_rate_limiter=admin_limiter, key="job-artifacts")
        _require_admin_token(settings=settings, authorization=authorization)
        return {
            "job_id": job_id,
            "artifacts": [
                _artifact_ref_response(ref) for ref in store.artifact_refs_for_job(job_id)
            ],
        }

    @app.get("/admin/lifecycle-events")
    def list_lifecycle_events(
        authorization: str | None = Header(default=None),
        limit: int = 50,
    ) -> dict[str, Any]:
        _require_admin_rate_limit(admin_rate_limiter=admin_limiter, key="lifecycle-events")
        _require_admin_token(settings=settings, authorization=authorization)
        safe_limit = _bounded_limit(limit)
        return {
            "events": [
                _lifecycle_event_response(event)
                for event in store.recent_lifecycle_events(limit=safe_limit)
            ]
        }

    @app.get("/admin/jobs")
    def list_jobs(
        authorization: str | None = Header(default=None),
        limit: int = 50,
    ) -> dict[str, Any]:
        _require_admin_rate_limit(admin_rate_limiter=admin_limiter, key="jobs")
        _require_admin_token(settings=settings, authorization=authorization)
        safe_limit = _bounded_limit(limit)
        return {
            "jobs": [
                _fulfillment_job_response(job)
                for job in store.recent_fulfillment_jobs(limit=safe_limit)
            ]
        }

    @app.get("/admin", response_class=HTMLResponse)
    def admin_console(authorization: str | None = Header(default=None)) -> HTMLResponse:
        _require_admin_console_credentials(settings=settings, authorization=authorization)
        jobs = store.recent_fulfillment_jobs(limit=25)
        events = store.recent_lifecycle_events(limit=25)
        artifact_refs_by_job = {job.job_id: store.artifact_refs_for_job(job.job_id) for job in jobs}
        return HTMLResponse(
            _admin_console_html(
                jobs=jobs,
                events=events,
                artifact_refs_by_job=artifact_refs_by_job,
            )
        )

    @app.get("/admin/artifacts/{artifact_id}", response_class=HTMLResponse)
    def admin_console_artifact(
        artifact_id: int,
        authorization: str | None = Header(default=None),
    ) -> HTMLResponse:
        _require_admin_console_credentials(settings=settings, authorization=authorization)
        try:
            artifact = store.get_artifact_blob(artifact_id)
        except KeyError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="artifact not found",
            ) from exc
        return HTMLResponse(_admin_artifact_html(artifact))

    return app


def _rate_limiter(*, max_requests: int, window_seconds: int) -> InMemoryRateLimiter | None:
    if max_requests < 1 or window_seconds < 1:
        return None
    return InMemoryRateLimiter(max_requests=max_requests, window_seconds=window_seconds)


def _artifact_blob_response(artifact: ArtifactBlobRecord) -> dict[str, Any]:
    return {
        "id": artifact.id,
        "job_id": artifact.job_id,
        "story_number": artifact.story_number,
        "artifact_kind": artifact.artifact_kind,
        "schema_version": artifact.schema_version,
        "sha256": artifact.sha256,
        "created_at": _json_timestamp(artifact.created_at),
        "payload": artifact.payload_json,
    }


def _artifact_ref_response(ref: ArtifactRefRecord) -> dict[str, Any]:
    return {
        "id": ref.id,
        "job_id": ref.job_id,
        "artifact_kind": ref.artifact_kind,
        "path": ref.path,
        "sha256": ref.sha256,
        "artifact_id": ref.artifact_id,
        "created_at": _json_timestamp(ref.created_at),
    }


def _lifecycle_event_response(event: LifecycleEventRecord) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "story_number": event.story_number,
        "correlation_id": event.correlation_id,
        "received_at": _json_timestamp(event.received_at),
        "validation_status": event.validation_status,
    }


def _fulfillment_job_response(job: FulfillmentJobRecord) -> dict[str, Any]:
    return {
        "job_id": job.job_id,
        "event_id": job.event_id,
        "story_number": job.story_number,
        "status": job.status,
        "attempt_count": job.attempt_count,
        "created_at": _json_timestamp(job.created_at),
        "updated_at": _json_timestamp(job.updated_at),
        "locked_by": job.locked_by,
        "locked_at": _json_timestamp(job.locked_at) if job.locked_at is not None else None,
        "correlation_id": job.correlation_id,
        "last_error": _redact_diagnostic_text(job.last_error),
    }


def _admin_console_html(
    *,
    jobs: list[FulfillmentJobRecord],
    events: list[LifecycleEventRecord],
    artifact_refs_by_job: dict[str, list[ArtifactRefRecord]],
) -> str:
    job_rows = "\n".join(
        _admin_job_row(job, artifact_refs_by_job.get(job.job_id, [])) for job in jobs
    )
    event_rows = "\n".join(_admin_event_row(event) for event in events)
    if not job_rows:
        job_rows = '<tr><td colspan="8" class="empty">No fulfillment jobs found.</td></tr>'
    if not event_rows:
        event_rows = '<tr><td colspan="5" class="empty">No lifecycle events found.</td></tr>'
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>JEDI Admin Console</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f8fa;
      --panel: #ffffff;
      --border: #d8dee4;
      --text: #24292f;
      --muted: #57606a;
      --accent: #0969da;
      --error: #b42318;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Arial, Helvetica, sans-serif;
      font-size: 14px;
    }}
    header {{
      background: var(--panel);
      border-bottom: 1px solid var(--border);
      padding: 18px 24px;
    }}
    h1 {{
      margin: 0 0 4px;
      font-size: 22px;
      font-weight: 700;
    }}
    header p {{
      margin: 0;
      color: var(--muted);
    }}
    main {{
      padding: 24px;
      display: grid;
      gap: 24px;
    }}
    section {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
    }}
    h2 {{
      margin: 0;
      padding: 14px 16px;
      border-bottom: 1px solid var(--border);
      font-size: 16px;
    }}
    .table-wrap {{ overflow-x: auto; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      min-width: 920px;
    }}
    th, td {{
      padding: 10px 12px;
      border-bottom: 1px solid var(--border);
      text-align: left;
      vertical-align: top;
    }}
    th {{
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
    }}
    code {{
      font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
      font-size: 12px;
    }}
    a {{ color: var(--accent); }}
    .muted {{ color: var(--muted); }}
    .error {{ color: var(--error); }}
    .empty {{
      color: var(--muted);
      text-align: center;
      padding: 22px;
    }}
  </style>
</head>
<body>
  <header>
    <h1>JEDI Admin Console</h1>
    <p>Read-only operational view. ServiceNow remains the user work surface.</p>
  </header>
  <main>
    <section>
      <h2>Fulfillment Jobs</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Job</th>
              <th>Story</th>
              <th>Correlation</th>
              <th>Status</th>
              <th>Attempts</th>
              <th>Updated</th>
              <th>Locked By</th>
              <th>Last Error</th>
              <th>Artifacts</th>
            </tr>
          </thead>
          <tbody>{job_rows}</tbody>
        </table>
      </div>
    </section>
    <section>
      <h2>Lifecycle Events</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Event</th>
              <th>Type</th>
              <th>Story</th>
              <th>Correlation</th>
              <th>Received</th>
              <th>Validation</th>
            </tr>
          </thead>
          <tbody>{event_rows}</tbody>
        </table>
      </div>
    </section>
  </main>
</body>
</html>"""


def _admin_job_row(job: FulfillmentJobRecord, refs: list[ArtifactRefRecord]) -> str:
    artifact_links = ", ".join(_admin_artifact_link(ref) for ref in refs)
    if not artifact_links:
        artifact_links = '<span class="muted">None</span>'
    last_error = _html(job.last_error or "")
    if last_error:
        last_error = f'<span class="error">{last_error}</span>'
    else:
        last_error = '<span class="muted">None</span>'
    return (
        "<tr>"
        f"<td><code>{_html(job.job_id)}</code></td>"
        f"<td>{_html(job.story_number)}</td>"
        f"<td><code>{_html(job.correlation_id or '')}</code></td>"
        f"<td>{_html(job.status)}</td>"
        f"<td>{job.attempt_count}</td>"
        f"<td>{_html(_json_timestamp(job.updated_at))}</td>"
        f"<td>{_html(job.locked_by or '')}</td>"
        f"<td>{last_error}</td>"
        f"<td>{artifact_links}</td>"
        "</tr>"
    )


def _admin_event_row(event: LifecycleEventRecord) -> str:
    return (
        "<tr>"
        f"<td><code>{_html(event.event_id)}</code></td>"
        f"<td>{_html(event.event_type)}</td>"
        f"<td>{_html(event.story_number)}</td>"
        f"<td><code>{_html(event.correlation_id or '')}</code></td>"
        f"<td>{_html(_json_timestamp(event.received_at))}</td>"
        f"<td>{_html(event.validation_status)}</td>"
        "</tr>"
    )


def _admin_artifact_link(ref: ArtifactRefRecord) -> str:
    label = _html(ref.artifact_kind)
    if ref.artifact_id is None:
        return f"<span>{label}</span>"
    return f'<a href="/admin/artifacts/{ref.artifact_id}">{label}</a>'


def _admin_artifact_html(artifact: ArtifactBlobRecord) -> str:
    payload_json = json.dumps(artifact.payload_json, indent=2, sort_keys=True)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Artifact {artifact.id} - JEDI Admin Console</title>
  <style>
    body {{
      margin: 0;
      background: #f6f8fa;
      color: #24292f;
      font-family: Arial, Helvetica, sans-serif;
      font-size: 14px;
    }}
    header {{
      background: #ffffff;
      border-bottom: 1px solid #d8dee4;
      padding: 18px 24px;
    }}
    main {{ padding: 24px; }}
    h1 {{ margin: 0 0 4px; font-size: 22px; }}
    dl {{
      display: grid;
      grid-template-columns: max-content 1fr;
      gap: 8px 14px;
      margin: 0 0 20px;
    }}
    dt {{ color: #57606a; font-weight: 700; }}
    dd {{ margin: 0; }}
    pre {{
      background: #ffffff;
      border: 1px solid #d8dee4;
      border-radius: 8px;
      padding: 16px;
      overflow: auto;
      white-space: pre-wrap;
    }}
    a {{ color: #0969da; }}
  </style>
</head>
<body>
  <header>
    <h1>Artifact {artifact.id}</h1>
    <a href="/admin">Back to Admin Console</a>
  </header>
  <main>
    <dl>
      <dt>Kind</dt><dd>{_html(artifact.artifact_kind)}</dd>
      <dt>Story</dt><dd>{_html(artifact.story_number)}</dd>
      <dt>Job</dt><dd>{_html(artifact.job_id)}</dd>
      <dt>Schema</dt><dd>{_html(artifact.schema_version)}</dd>
      <dt>Created</dt><dd>{_html(_json_timestamp(artifact.created_at))}</dd>
      <dt>SHA-256</dt><dd><code>{_html(artifact.sha256)}</code></dd>
    </dl>
    <pre>{_html(payload_json)}</pre>
  </main>
</body>
</html>"""


def _html(value: str) -> str:
    return html.escape(value, quote=True)


def _bounded_limit(limit: int) -> int:
    return min(max(limit, 1), 100)


def _json_timestamp(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")
