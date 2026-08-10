"""CLI command implementations for artifact handoff and delivery attachment."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from pathlib import Path

from pydantic import ValidationError

from jedi_devproject.artifact_handoff import (
    ArtifactKind,
    build_artifact_handoff_report,
    build_artifact_handoff_work_note,
    build_reviewed_delivery_artifact_job,
    delivery_attachment_jobs_from_report,
)
from jedi_devproject.artifacts import (
    ArtifactWriteError,
    artifact_sha256_file,
    write_delivery_attachment_audit,
    write_json_artifact_once,
    write_reviewed_delivery_lifecycle_manifest,
    write_text_artifact_once,
)
from jedi_devproject.cli_io import (
    load_json_list,
    load_json_object,
    render_cli_error,
    render_summary,
)
from jedi_devproject.external_build import (
    ExternalBuildPipelineResult,
    SuccessfulBuildRequiredError,
    reviewed_delivery_jobs_from_build_result,
    writeback_job_from_build_result,
)
from jedi_devproject.lifecycle_events import (
    LifecycleStateChangeEvent,
    plan_story_ready_lifecycle_event,
)
from jedi_devproject.models import Story
from jedi_devproject.servicenow import ServiceNowClient, UrllibTransport

CLI_STORY_LOOKUP_RESULT_UNSAFE_REASON = "story_lookup_result_unsafe"


def _client_from_env(env_file: Path) -> ServiceNowClient:
    # Resolved through the CLI facade so patches against
    # jedi_devproject.cli.servicenow_client_from_env keep intercepting it.
    from jedi_devproject import cli

    return cli.servicenow_client_from_env(env_file, transport=UrllibTransport())


def process_external_build_result_command(args: argparse.Namespace) -> int:
    try:
        build_result = ExternalBuildPipelineResult.model_validate(
            load_json_object(args.result_file)
        )
    except (ValidationError, ValueError) as exc:
        print(
            f"external_build_results=0 reason=invalid_build_result detail={render_cli_error(exc)}"
        )
        return 1

    writeback_jobs = [writeback_job_from_build_result(build_result, from_state=args.from_state)]
    try:
        external_delivery_jobs = reviewed_delivery_jobs_from_build_result(build_result)
    except SuccessfulBuildRequiredError:
        external_delivery_jobs = []
    except ValueError as exc:
        print(f"external_build_results=0 reason={render_cli_error(exc)}")
        return 1

    writeback_path = write_json_artifact_once(
        args.writeback_job_root,
        filename=f"{args.run_id}.json",
        payload=writeback_jobs,
    )
    delivery_path = None
    if external_delivery_jobs:
        delivery_path = write_json_artifact_once(
            args.delivery_job_root,
            filename=f"{args.run_id}.json",
            payload=external_delivery_jobs,
        )

    delivery_path_text = "" if delivery_path is None else f" delivery_job_file={delivery_path}"
    print(
        "external_build_results=1 "
        f"writeback_jobs={len(writeback_jobs)} "
        f"reviewed_delivery_jobs={len(external_delivery_jobs)} "
        f"writeback_job_file={writeback_path}"
        f"{delivery_path_text}"
    )
    return 0


def process_lifecycle_event_command(args: argparse.Namespace) -> int:
    try:
        lifecycle_event = LifecycleStateChangeEvent.model_validate(
            load_json_object(args.event_file)
        )
    except (ValidationError, ValueError) as exc:
        print(
            f"lifecycle_event_plans=0 reason=invalid_lifecycle_event detail={render_cli_error(exc)}"
        )
        return 1

    lifecycle_plan = plan_story_ready_lifecycle_event(lifecycle_event)
    plan_path = write_json_artifact_once(
        args.plan_root,
        filename=f"{args.run_id}.json",
        payload={
            "run_id": args.run_id,
            "event": lifecycle_event.model_dump(mode="json"),
            "plan": lifecycle_plan.model_dump(mode="json"),
        },
    )
    print(
        "lifecycle_event_plans=1 "
        f"story_number={lifecycle_plan.story_number} "
        f"should_evaluate={lifecycle_plan.should_evaluate} "
        f"claim_state={lifecycle_plan.claim_state} "
        f"path={plan_path}"
    )
    return 0


def plan_artifact_handoff_command(args: argparse.Namespace) -> int:
    report = build_artifact_handoff_report(
        run_id=args.run_id,
        story_number=args.story_number,
        artifacts=load_json_list(args.jobs_file, "artifact handoff jobs file"),
    )
    write_json_artifact_once(
        args.report_root,
        filename=f"{args.run_id}.json",
        payload=report,
    )
    print(render_summary({"handoff_plans": report["summary"]["total"], **report["summary"]}))
    return 0


def review_delivery_artifact_command(args: argparse.Namespace) -> int:
    try:
        job = build_reviewed_delivery_artifact_job(
            story_number=args.story_number,
            artifact_kind=ArtifactKind(args.artifact_kind),
            artifact_path=args.artifact_path,
            reviewer_id=args.reviewer_id,
        )
    except ValueError as exc:
        print(f"reviewed_delivery_artifacts=0 reason={render_cli_error(exc)}")
        return 1
    job_path = write_json_artifact_once(
        args.job_root,
        filename=f"{args.run_id}.json",
        payload=[job],
    )
    print(f"reviewed_delivery_artifacts=1 story_number={args.story_number} path={job_path}")
    return 0


def write_artifact_handoff_summary_command(args: argparse.Namespace) -> int:
    report = load_json_object(args.report_file)
    try:
        story_number = _handoff_report_story_number(report)
        work_note = build_artifact_handoff_work_note(
            report=report,
            report_path=args.report_file,
        )
    except (KeyError, TypeError, ValueError):
        print("handoff_summary_written=False reason=artifact_handoff_report_invalid")
        return 1
    if not args.apply:
        print(f"handoff_summary_written=False story_number={story_number} dry_run=True")
        return 0
    if args.confirm_story_number != story_number:
        print(
            "handoff_summary_written=False "
            f"story_number={story_number} reason=confirmation_mismatch"
        )
        return 1
    if not args.actor_id:
        print(
            "handoff_summary_written=False "
            f"story_number={story_number} reason=actor_identity_required"
        )
        return 1
    client = _client_from_env(args.env_file)
    try:
        stories = _cli_story_lookup_results(
            client.fetch_stories(sysparm_query=f"number={story_number}", limit=1)
        )
    except ValueError:
        print(
            "handoff_summary_written=False "
            f"story_number={story_number} reason={CLI_STORY_LOOKUP_RESULT_UNSAFE_REASON}"
        )
        return 1
    if not stories:
        print(f"handoff_summary_written=False story_number={story_number} reason=story_not_found")
        return 1
    client.update_story_fields(stories[0].sys_id, {"work_notes": work_note})
    print(f"handoff_summary_written=True story_number={story_number}")
    return 0


def attach_delivery_artifacts_command(args: argparse.Namespace) -> int:
    report = load_json_object(args.report_file)
    try:
        story_number = _handoff_report_story_number(report)
        delivery_jobs = delivery_attachment_jobs_from_report(report)
    except ValueError as exc:
        print(
            "delivery_attachments_planned=0 delivery_attachments_applied=0 "
            f"reason={render_cli_error(exc)}"
        )
        return 1
    for delivery_job in delivery_jobs:
        artifact_path = Path(delivery_job["artifact_path"])
        if not artifact_path.exists():
            print(
                f"delivery_attachments_planned={len(delivery_jobs)} "
                "delivery_attachments_applied=0 reason=artifact_missing"
            )
            return 1
        artifact_hash = artifact_sha256_file(artifact_path)
        if artifact_hash != delivery_job["artifact_sha256"]:
            print(
                f"delivery_attachments_planned={len(delivery_jobs)} "
                "delivery_attachments_applied=0 reason=artifact_hash_mismatch"
            )
            return 1
    if not args.apply:
        print(
            f"delivery_attachments_planned={len(delivery_jobs)} "
            "delivery_attachments_applied=0 dry_run=True"
        )
        return 0
    if args.confirm_story_number != story_number:
        print(
            f"delivery_attachments_planned={len(delivery_jobs)} "
            "delivery_attachments_applied=0 reason=confirmation_mismatch"
        )
        return 1
    if not args.actor_id:
        print(
            f"delivery_attachments_planned={len(delivery_jobs)} "
            "delivery_attachments_applied=0 reason=actor_identity_required"
        )
        return 1
    if args.audit_root is None or args.run_id is None:
        print(
            f"delivery_attachments_planned={len(delivery_jobs)} "
            "delivery_attachments_applied=0 reason=attachment_audit_required"
        )
        return 1
    if (args.audit_root / f"{args.run_id}.json").exists():
        print(
            f"delivery_attachments_planned={len(delivery_jobs)} "
            "delivery_attachments_applied=0 reason=attachment_audit_already_exists"
        )
        return 1
    client = _client_from_env(args.env_file)
    try:
        stories = _cli_story_lookup_results(
            client.fetch_stories(sysparm_query=f"number={story_number}", limit=1)
        )
    except ValueError:
        print(
            f"delivery_attachments_planned={len(delivery_jobs)} "
            "delivery_attachments_applied=0 "
            f"reason={CLI_STORY_LOOKUP_RESULT_UNSAFE_REASON}"
        )
        return 1
    if not stories:
        print(
            f"delivery_attachments_planned={len(delivery_jobs)} "
            "delivery_attachments_applied=0 reason=story_not_found"
        )
        return 1
    attachment_results: list[dict[str, str]] = []
    for delivery_job in delivery_jobs:
        artifact_path = Path(delivery_job["artifact_path"])
        attachment = client.attach_story_file(
            stories[0].sys_id,
            file_path=artifact_path,
            file_name=f"{delivery_job['attachment_label']} - {artifact_path.name}",
            content_type=_content_type_for_artifact(artifact_path),
        )
        attachment_results.append(
            {
                "artifact_kind": _delivery_job_text(delivery_job, "artifact_kind"),
                "artifact_path": _delivery_job_text(delivery_job, "artifact_path"),
                "artifact_sha256": _delivery_job_text(delivery_job, "artifact_sha256"),
                "attachment_label": _delivery_job_text(delivery_job, "attachment_label"),
                "attachment_sys_id": _attachment_response_sys_id(attachment),
            }
        )
    audit_path = write_delivery_attachment_audit(
        args.audit_root,
        run_id=args.run_id,
        story_number=story_number,
        actor_id=args.actor_id,
        report_path=args.report_file,
        attachments=attachment_results,
    )
    print(
        f"delivery_attachments_planned={len(delivery_jobs)} "
        f"delivery_attachments_applied={len(delivery_jobs)} "
        f"attachment_audit={audit_path}"
    )
    return 0


def _handoff_report_story_number(report: dict[str, object]) -> str:
    story_number = report.get("story_number")
    if type(story_number) is not str or not story_number:
        raise ValueError("artifact_handoff_report_invalid")
    return story_number


def _cli_story_lookup_results(stories: object) -> list[Story]:
    if type(stories) is not list:
        raise ValueError(CLI_STORY_LOOKUP_RESULT_UNSAFE_REASON)
    for story in stories:
        if type(story) is not Story:
            raise ValueError(CLI_STORY_LOOKUP_RESULT_UNSAFE_REASON)
    return stories


def _delivery_job_text(delivery_job: Mapping[str, object], key: str) -> str:
    value = delivery_job.get(key)
    if type(value) is not str:
        raise ValueError("artifact_handoff_report_invalid")
    return value


def _attachment_response_sys_id(attachment: dict[str, object]) -> str:
    sys_id = attachment.get("sys_id")
    if type(sys_id) is not str or not sys_id:
        return "[attachment sys_id unavailable]"
    return sys_id


def run_delivery_artifact_smoke_command(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> int:
    export_dir = args.artifact_root / "exports" / args.run_id
    export_dir.mkdir(parents=True, exist_ok=True)
    export_path = export_dir / f"{args.story_number}.xml"
    try:
        write_text_artifact_once(
            export_path,
            (
                f'<placeholder_update_set story_number="{args.story_number}" '
                'artifact_kind="update_set_xml">'
                "Attachment gate smoke only."
                "</placeholder_update_set>"
            ),
        )
    except ArtifactWriteError:
        parser.error(f"delivery smoke artifact already exists: {export_path}")
    handoff_report = build_artifact_handoff_report(
        run_id=args.run_id,
        story_number=args.story_number,
        artifacts=[
            {
                "artifact_kind": "update_set_xml",
                "artifact_path": str(export_path),
                "approved_for_delivery": True,
                "delivery_contract": "smoke_placeholder",
            }
        ],
    )
    write_json_artifact_once(
        args.artifact_root / "artifact-handoff-reports",
        filename=f"{args.run_id}.json",
        payload=handoff_report,
    )
    print(
        "delivery_artifact_created=True "
        f"delivery_attachments_planned={handoff_report['summary']['attach_to_servicenow']} "
        "delivery_attachments_applied=0"
    )
    return 0


def run_reviewed_delivery_smoke_command(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> int:
    export_dir = args.artifact_root / "exports" / args.run_id
    export_dir.mkdir(parents=True, exist_ok=True)
    export_path = export_dir / f"{args.story_number}.xml"
    try:
        write_text_artifact_once(
            export_path,
            (
                f'<unload story_number="{args.story_number}" '
                'artifact_kind="update_set_xml">'
                '<sys_update_xml action="INSERT_OR_UPDATE" />'
                "</unload>"
            ),
        )
    except ArtifactWriteError:
        parser.error(f"reviewed delivery smoke artifact already exists: {export_path}")
    reviewed_job = build_reviewed_delivery_artifact_job(
        story_number=args.story_number,
        artifact_kind=ArtifactKind.UPDATE_SET_XML,
        artifact_path=export_path,
        reviewer_id=args.reviewer_id,
    )
    reviewed_job_path = write_json_artifact_once(
        args.artifact_root / "reviewed-delivery-jobs",
        filename=f"{args.run_id}.json",
        payload=[reviewed_job],
    )
    handoff_report = build_artifact_handoff_report(
        run_id=args.run_id,
        story_number=args.story_number,
        artifacts=[reviewed_job],
    )
    handoff_report_path = write_json_artifact_once(
        args.artifact_root / "artifact-handoff-reports",
        filename=f"{args.run_id}.json",
        payload=handoff_report,
    )
    write_reviewed_delivery_lifecycle_manifest(
        args.artifact_root / "reviewed-delivery-lifecycle-manifests",
        run_id=args.run_id,
        story_number=args.story_number,
        delivery_artifact_path=export_path,
        reviewed_delivery_job_path=reviewed_job_path,
        artifact_handoff_report_path=handoff_report_path,
        delivery_attachment_plan={
            "dry_run": True,
            "planned": handoff_report["summary"]["attach_to_servicenow"],
            "applied": 0,
        },
    )
    print(
        "reviewed_delivery_artifacts=1 "
        f"handoff_plans={handoff_report['summary']['total']} "
        f"delivery_attachments_planned={handoff_report['summary']['attach_to_servicenow']} "
        "delivery_attachments_applied=0 "
        "lifecycle_manifest_written=True"
    )
    return 0


def _content_type_for_artifact(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".xml":
        return "application/xml"
    if suffix == ".json":
        return "application/json"
    if suffix == ".zip":
        return "application/zip"
    return "application/octet-stream"
