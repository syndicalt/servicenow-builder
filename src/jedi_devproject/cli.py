from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path

from jedi_devproject import __version__
from jedi_devproject.artifact_handoff import (
    build_artifact_handoff_report,
    build_artifact_handoff_work_note,
    delivery_attachment_jobs_from_report,
)
from jedi_devproject.artifacts import (
    write_candidate_artifact,
    write_delivery_attachment_audit,
    write_json_artifact_once,
    write_lifecycle_manifest,
)
from jedi_devproject.bootstrap import apply_bootstrap_fields, plan_bootstrap_fields
from jedi_devproject.implementation_packet import (
    IMPLEMENTATION_PACKET_TASK,
    build_implementation_packet,
    generate_implementation_update_set_candidate,
)
from jedi_devproject.models import DataClassification, ProviderPolicy, ProviderStatus, Story
from jedi_devproject.pipeline import PipelineInputs, run_pipeline
from jedi_devproject.rag import Document, RagDomain, SpecializedRags
from jedi_devproject.safety import AllowlistPolicy, StoryType
from jedi_devproject.servicenow import UrllibTransport, servicenow_client_from_env
from jedi_devproject.writeback import ActorType, ExternalBuildStatus
from jedi_devproject.writeback_orchestration import (
    WritebackClient,
    WritebackExecutionRequest,
    WritebackExecutionResult,
    build_writeback_batch_report,
    evaluate_writeback_capability,
    execute_writeback,
    load_writeback_requests,
    run_writeback_batch,
    verify_writeback,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jedi-devproject")
    parser.add_argument("--version", action="store_true", help="Print the project version.")
    subparsers = parser.add_subparsers(dest="command")
    run_local = subparsers.add_parser("run-local", help="Run the local candidate pipeline.")
    run_local.add_argument("--sample-file", type=Path, required=True)
    run_local.add_argument("--artifact-root", type=Path, default=Path("artifacts"))
    run_local.add_argument("--run-id", required=True)
    run_pdi = subparsers.add_parser("run-pdi", help="Run the pipeline from ServiceNow PDI.")
    run_pdi.add_argument("--env-file", type=Path, default=Path(".env"))
    run_pdi.add_argument("--artifact-root", type=Path, default=Path("artifacts"))
    run_pdi.add_argument("--run-id", required=True)
    run_pdi.add_argument("--limit", type=int, default=5)
    run_pdi.add_argument("--project-sys-id")
    run_pdi.add_argument("--sysparm-query")
    build_packet = subparsers.add_parser(
        "build-implementation-packet",
        help="Build reviewable LLM implementation packet artifacts from local stories.",
    )
    build_packet.add_argument("--sample-file", type=Path)
    build_packet.add_argument("--env-file", type=Path, default=Path(".env"))
    build_packet.add_argument("--story-number")
    build_packet.add_argument("--artifact-root", type=Path, default=Path("artifacts"))
    build_packet.add_argument("--run-id", required=True)
    build_candidate = subparsers.add_parser(
        "build-implementation-candidate",
        help=(
            "Build a validated implementation candidate artifact from an explicit "
            "provider response."
        ),
    )
    build_candidate.add_argument("--sample-file", type=Path)
    build_candidate.add_argument("--env-file", type=Path, default=Path(".env"))
    build_candidate.add_argument("--story-number")
    build_candidate.add_argument("--provider-response-file", type=Path, required=True)
    build_candidate.add_argument("--artifact-root", type=Path, default=Path("artifacts"))
    build_candidate.add_argument("--run-id", required=True)
    run_candidates = subparsers.add_parser(
        "run-implementation-candidates",
        help="Run implementation candidate jobs from a JSON file.",
    )
    run_candidates.add_argument("--jobs-file", type=Path, required=True)
    run_candidates.add_argument("--artifact-root", type=Path, default=Path("artifacts"))
    run_candidates.add_argument("--batch-report-root", type=Path, required=True)
    run_candidates.add_argument("--run-id", required=True)
    lifecycle_smoke = subparsers.add_parser(
        "run-lifecycle-smoke",
        help="Run a dry-run lifecycle smoke test from story fetch through writeback plan.",
    )
    lifecycle_smoke.add_argument("--env-file", type=Path, default=Path(".env"))
    lifecycle_smoke.add_argument("--story-number", required=True)
    lifecycle_smoke.add_argument("--provider-response-file", type=Path, required=True)
    lifecycle_smoke.add_argument("--artifact-root", type=Path, default=Path("artifacts"))
    lifecycle_smoke.add_argument("--run-id", required=True)
    lifecycle_smoke.add_argument("--build-reference", required=True)
    lifecycle_smoke.add_argument("--from-state", required=True)
    plan_writeback = subparsers.add_parser(
        "plan-writeback",
        help="Plan ServiceNow writeback for an external build result without applying it.",
    )
    plan_writeback.add_argument("--env-file", type=Path, default=Path(".env"))
    plan_writeback.add_argument("--story-number", required=True)
    plan_writeback.add_argument("--build-reference", required=True)
    plan_writeback.add_argument("--artifact-url")
    plan_writeback.add_argument(
        "--build-status",
        choices=[status.value for status in ExternalBuildStatus],
        default=ExternalBuildStatus.SUCCEEDED.value,
    )
    plan_writeback.add_argument("--from-state", required=True)
    plan_writeback.add_argument("--apply", action="store_true")
    plan_writeback.add_argument("--confirm-story-number")
    plan_writeback.add_argument(
        "--actor-type",
        choices=[actor_type.value for actor_type in ActorType],
        default=ActorType.SERVICE.value,
    )
    plan_writeback.add_argument("--actor-id")
    plan_writeback.add_argument("--execution-id")
    plan_writeback.add_argument("--audit-root", type=Path)
    plan_writeback.add_argument("--manifest-root", type=Path)
    plan_writeback.add_argument("--packet-path", type=Path)
    plan_writeback.add_argument("--candidate-path", type=Path)
    plan_writeback.add_argument("--candidate-batch-path", type=Path)
    check_writeback = subparsers.add_parser(
        "check-writeback-capability",
        help="Check whether the ServiceNow instance supports structured writeback.",
    )
    check_writeback.add_argument("--env-file", type=Path, default=Path(".env"))
    verify_writeback_parser = subparsers.add_parser(
        "verify-writeback",
        help="Read ServiceNow and verify a completed structured writeback.",
    )
    verify_writeback_parser.add_argument("--env-file", type=Path, default=Path(".env"))
    verify_writeback_parser.add_argument("--story-number", required=True)
    verify_writeback_parser.add_argument("--build-reference", required=True)
    verify_writeback_parser.add_argument("--artifact-url")
    lifecycle_manifest = subparsers.add_parser(
        "record-lifecycle-manifest",
        help="Write a manifest tying lifecycle phase artifacts together.",
    )
    lifecycle_manifest.add_argument("--run-id", required=True)
    lifecycle_manifest.add_argument("--story-number", required=True)
    lifecycle_manifest.add_argument("--build-reference", required=True)
    lifecycle_manifest.add_argument("--packet-path", type=Path, required=True)
    lifecycle_manifest.add_argument("--candidate-path", type=Path, required=True)
    lifecycle_manifest.add_argument("--writeback-audit-path", type=Path)
    lifecycle_manifest.add_argument("--verification-verified", action="store_true")
    lifecycle_manifest.add_argument("--verification-state")
    lifecycle_manifest.add_argument("--manifest-root", type=Path, required=True)
    handoff = subparsers.add_parser(
        "plan-artifact-handoff",
        help="Write a report describing artifact attachment and link decisions.",
    )
    handoff.add_argument("--run-id", required=True)
    handoff.add_argument("--story-number", required=True)
    handoff.add_argument("--jobs-file", type=Path, required=True)
    handoff.add_argument("--report-root", type=Path, required=True)
    handoff_summary = subparsers.add_parser(
        "write-artifact-handoff-summary",
        help="Write a ServiceNow work note summarizing an artifact handoff report.",
    )
    handoff_summary.add_argument("--env-file", type=Path, default=Path(".env"))
    handoff_summary.add_argument("--report-file", type=Path, required=True)
    handoff_summary.add_argument("--apply", action="store_true")
    handoff_summary.add_argument("--confirm-story-number")
    handoff_summary.add_argument("--actor-id")
    attach_delivery = subparsers.add_parser(
        "attach-delivery-artifacts",
        help="Attach approved delivery artifacts from a handoff report.",
    )
    attach_delivery.add_argument("--env-file", type=Path, default=Path(".env"))
    attach_delivery.add_argument("--report-file", type=Path, required=True)
    attach_delivery.add_argument("--apply", action="store_true")
    attach_delivery.add_argument("--confirm-story-number")
    attach_delivery.add_argument("--actor-id")
    attach_delivery.add_argument("--audit-root", type=Path)
    attach_delivery.add_argument("--run-id")
    delivery_smoke = subparsers.add_parser(
        "run-delivery-artifact-smoke",
        help="Create a local placeholder delivery artifact and plan attachment.",
    )
    delivery_smoke.add_argument("--run-id", required=True)
    delivery_smoke.add_argument("--story-number", required=True)
    delivery_smoke.add_argument("--artifact-root", type=Path, default=Path("artifacts"))
    plan_bootstrap = subparsers.add_parser(
        "plan-bootstrap-fields",
        help="Plan missing ServiceNow bootstrap table fields without applying changes.",
    )
    plan_bootstrap.add_argument("--env-file", type=Path, default=Path(".env"))
    apply_bootstrap = subparsers.add_parser(
        "apply-bootstrap-fields",
        help="Create missing ServiceNow bootstrap table fields with confirmation.",
    )
    apply_bootstrap.add_argument("--env-file", type=Path, default=Path(".env"))
    apply_bootstrap.add_argument("--confirm-table")
    apply_bootstrap.add_argument("--confirm-fields", action="store_true")
    apply_bootstrap.add_argument("--audit-root", type=Path, required=True)
    apply_bootstrap.add_argument("--run-id", default="bootstrap-fields")
    run_writeback = subparsers.add_parser(
        "run-writeback-batch",
        help="Run structured writeback jobs from a JSON file.",
    )
    run_writeback.add_argument("--env-file", type=Path, default=Path(".env"))
    run_writeback.add_argument("--jobs-file", type=Path, required=True)
    run_writeback.add_argument("--apply", action="store_true")
    run_writeback.add_argument(
        "--actor-type",
        choices=[actor_type.value for actor_type in ActorType],
        default=ActorType.SERVICE.value,
    )
    run_writeback.add_argument("--actor-id", required=True)
    run_writeback.add_argument("--execution-id")
    run_writeback.add_argument("--audit-root", type=Path, required=True)
    run_writeback.add_argument("--batch-report-root", type=Path, required=True)
    args = parser.parse_args(argv)

    if args.version:
        print(f"jedi-devproject-0 {__version__}")
        return 0

    if args.command == "run-local":
        stories = _load_sample_stories(args.sample_file)
        result = run_pipeline(
            PipelineInputs(
                stories=stories,
                policy=_default_policy(),
                rags=_default_rags(),
                artifact_root=args.artifact_root,
                run_id=args.run_id,
            )
        )
        print(_render_summary(result.summary))
        return 0

    if args.command == "run-pdi":
        client = servicenow_client_from_env(args.env_file, transport=UrllibTransport())
        if args.sysparm_query:
            stories = client.fetch_stories(sysparm_query=args.sysparm_query, limit=args.limit)
        elif args.project_sys_id:
            stories = client.fetch_ready_stories(
                project_sys_id=args.project_sys_id,
                limit=args.limit,
            )
        else:
            stories = client.fetch_stories(limit=args.limit)
        result = run_pipeline(
            PipelineInputs(
                stories=stories,
                policy=_default_policy(),
                rags=_default_rags(),
                artifact_root=args.artifact_root,
                run_id=args.run_id,
            )
        )
        print(_render_summary(result.summary))
        return 0

    if args.command == "build-implementation-packet":
        stories = _load_stories_from_args(args, parser, "build-implementation-packet")
        if not stories:
            print("implementation_packets=0 reason=no_stories_found")
            return 1
        artifact_dir = args.artifact_root / args.run_id
        for story in stories:
            packet = build_implementation_packet(
                story=story,
                policy=_default_policy(),
                provider_policy=_default_implementation_provider_policy(),
                rags=_default_rags(),
            )
            write_json_artifact_once(
                artifact_dir,
                filename=f"{story.number}.json",
                payload=packet.to_model_payload(),
            )
        print(f"implementation_packets={len(stories)} run_id={args.run_id}")
        return 0

    if args.command == "build-implementation-candidate":
        stories = _load_stories_from_args(args, parser, "build-implementation-candidate")
        if not stories:
            print("implementation_candidates=0 reason=no_stories_found")
            return 1
        provider = StaticResponseProvider(_load_json_object(args.provider_response_file))
        for story in stories:
            candidate = generate_implementation_update_set_candidate(
                story=story,
                policy=_default_policy(),
                provider_policy=_default_implementation_provider_policy(),
                rags=_default_rags(),
                provider=provider,
            )
            write_candidate_artifact(
                args.artifact_root,
                run_id=args.run_id,
                candidate=candidate,
            )
        print(f"implementation_candidates={len(stories)} run_id={args.run_id}")
        return 0

    if args.command == "run-implementation-candidates":
        jobs = _load_implementation_candidate_jobs(args.jobs_file)
        if not jobs:
            print("total=0 built=0 blocked=0 reason=no_jobs")
            return 1
        built = 0
        blocked = 0
        outcomes: list[dict[str, object]] = []
        for job in jobs:
            stories = _load_sample_stories(job["sample_file"])
            provider = StaticResponseProvider(_load_json_object(job["provider_response_file"]))
            for story in stories:
                try:
                    candidate = generate_implementation_update_set_candidate(
                        story=story,
                        policy=_default_policy(),
                        provider_policy=_default_implementation_provider_policy(),
                        rags=_default_rags(),
                        provider=provider,
                    )
                    candidate_path = write_candidate_artifact(
                        args.artifact_root,
                        run_id=args.run_id,
                        candidate=candidate,
                    )
                    outcomes.append(
                        {
                            "story_number": candidate.story_number,
                            "status": "built",
                            "candidate_artifact": str(candidate_path),
                        }
                    )
                    built += 1
                except (RuntimeError, ValueError) as exc:
                    outcomes.append(
                        {
                            "story_number": story.number,
                            "status": "blocked",
                            "reason": str(exc),
                        }
                    )
                    blocked += 1
        summary = {"total": len(jobs), "built": built, "blocked": blocked}
        write_json_artifact_once(
            args.batch_report_root,
            filename=f"{args.run_id}.json",
            payload={
                "run_id": args.run_id,
                "summary": summary,
                "outcomes": outcomes,
            },
        )
        print(_render_summary(summary))
        return 0 if blocked == 0 else 1

    if args.command == "run-lifecycle-smoke":
        client = servicenow_client_from_env(args.env_file, transport=UrllibTransport())
        stories = client.fetch_stories(
            sysparm_query=f"number={args.story_number}",
            limit=1,
        )
        if not stories:
            print(
                "packet_built=0 candidate_built=0 "
                "writeback_allowed=False writeback_applied=False reason=no_stories_found"
            )
            return 1

        story = stories[0]
        packet = build_implementation_packet(
            story=story,
            policy=_default_policy(),
            provider_policy=_default_implementation_provider_policy(),
            rags=_default_rags(),
        )
        packet_root = args.artifact_root / "implementation-packets" / args.run_id
        write_json_artifact_once(
            packet_root,
            filename=f"{story.number}.json",
            payload=packet.to_model_payload(),
        )

        candidate = generate_implementation_update_set_candidate(
            story=story,
            policy=_default_policy(),
            provider_policy=_default_implementation_provider_policy(),
            rags=_default_rags(),
            provider=StaticResponseProvider(_load_json_object(args.provider_response_file)),
        )
        candidate_path = write_candidate_artifact(
            args.artifact_root / "implementation-candidates",
            run_id=args.run_id,
            candidate=candidate,
        )
        summary = {"total": 1, "built": 1, "blocked": 0}
        candidate_batch_path = write_json_artifact_once(
            args.artifact_root / "implementation-candidate-batches",
            filename=f"{args.run_id}.json",
            payload={
                "run_id": args.run_id,
                "summary": summary,
                "outcomes": [
                    {
                        "story_number": candidate.story_number,
                        "status": "built",
                        "candidate_artifact": str(candidate_path),
                    }
                ],
            },
        )

        writeback_result = execute_writeback(
            client,
            WritebackExecutionRequest(
                story_number=story.number,
                build_reference=args.build_reference,
                artifact_url=str(candidate_path),
                from_state=args.from_state,
                apply=False,
                execution_id=args.run_id,
            ),
        )
        write_lifecycle_manifest(
            args.artifact_root / "lifecycle-manifests",
            run_id=args.run_id,
            story_number=story.number,
            build_reference=args.build_reference,
            packet_path=packet_root / f"{story.number}.json",
            candidate_path=candidate_path,
            candidate_batch_path=candidate_batch_path,
            writeback_audit_path=writeback_result.audit_path,
            writeback={
                "allowed": writeback_result.allowed,
                "applied": writeback_result.applied,
                "idempotent": writeback_result.idempotent,
                "reasons": writeback_result.reasons or writeback_result.plan.reasons,
            },
            verification={
                "verified": False,
                "expected_state": None,
                "actual_fields": {},
                "reasons": ["dry_run_not_verified"],
            },
        )
        print(
            "packet_built=1 candidate_built=1 "
            f"writeback_allowed={writeback_result.allowed} "
            f"writeback_applied={writeback_result.applied}"
        )
        return 0 if writeback_result.allowed else 1

    if args.command == "plan-writeback":
        client = servicenow_client_from_env(args.env_file, transport=UrllibTransport())
        if args.manifest_root is not None and (
            args.packet_path is None or args.candidate_path is None
        ):
            parser.error(
                "plan-writeback --manifest-root requires --packet-path and --candidate-path"
            )
        writeback_result = execute_writeback(
            client,
            WritebackExecutionRequest(
                story_number=args.story_number,
                build_reference=args.build_reference,
                artifact_url=args.artifact_url,
                build_status=ExternalBuildStatus(args.build_status),
                from_state=args.from_state,
                apply=args.apply,
                confirm_story_number=args.confirm_story_number,
                actor_type=ActorType(args.actor_type),
                actor_id=args.actor_id,
                execution_id=args.execution_id,
                audit_root=args.audit_root,
            ),
        )
        plan = writeback_result.plan
        printable_fields = " ".join(
            f"{key}={value}" for key, value in sorted(plan.fields.items())
        )
        printable_reasons = " ".join(
            f"reason={reason.replace(' ', '_')}"
            for reason in [*plan.reasons, *writeback_result.reasons]
        )
        print(
            f"dry_run=True story_number={plan.story_number} "
            f"allowed={plan.allowed} {printable_fields} {printable_reasons}".strip()
        )
        if writeback_result.applied:
            print(f"applied=True story_number={plan.story_number}")
            if args.manifest_root is not None:
                _write_apply_lifecycle_manifest(
                    client=client,
                    manifest_root=args.manifest_root,
                    run_id=args.execution_id or args.build_reference,
                    story_number=plan.story_number,
                    build_reference=args.build_reference,
                    artifact_url=args.artifact_url,
                    packet_path=args.packet_path,
                    candidate_path=args.candidate_path,
                    candidate_batch_path=args.candidate_batch_path,
                    writeback_result=writeback_result,
                )
        elif args.apply and writeback_result.reasons:
            print(f"applied=False reason={writeback_result.reasons[-1]}")
        return (
            0
            if writeback_result.allowed and (not args.apply or writeback_result.applied)
            else 1
        )

    if args.command == "check-writeback-capability":
        client = servicenow_client_from_env(args.env_file, transport=UrllibTransport())
        capability = evaluate_writeback_capability(client)
        missing_fields = ",".join(capability.missing_fields)
        reasons = ",".join(capability.reasons)
        print(
            f"allowed={capability.allowed} "
            f"ready_for_testing_state={capability.ready_for_testing_state} "
            f"missing_fields={missing_fields} reasons={reasons}"
        )
        return 0 if capability.allowed else 1

    if args.command == "verify-writeback":
        client = servicenow_client_from_env(args.env_file, transport=UrllibTransport())
        verification = verify_writeback(
            client,
            story_number=args.story_number,
            build_reference=args.build_reference,
            artifact_url=args.artifact_url,
        )
        printable_fields = " ".join(
            f"{key}={value}" for key, value in sorted(verification.actual_fields.items())
        )
        printable_reasons = " ".join(
            f"reason={reason}" for reason in verification.reasons
        )
        print(
            f"verified={verification.verified} "
            f"story_number={verification.story_number} "
            f"expected_state={verification.expected_state} "
            f"{printable_fields} {printable_reasons}".strip()
        )
        return 0 if verification.verified else 1

    if args.command == "record-lifecycle-manifest":
        manifest_path = write_lifecycle_manifest(
            args.manifest_root,
            run_id=args.run_id,
            story_number=args.story_number,
            build_reference=args.build_reference,
            packet_path=args.packet_path,
            candidate_path=args.candidate_path,
            writeback_audit_path=args.writeback_audit_path,
            verification={
                "verified": args.verification_verified,
                "expected_state": args.verification_state,
                "actual_fields": (
                    {"state": args.verification_state}
                    if args.verification_state is not None
                    else {}
                ),
                "reasons": [] if args.verification_verified else ["not_verified"],
            },
        )
        print(
            "lifecycle_manifest_written=True "
            f"story_number={args.story_number} path={manifest_path}"
        )
        return 0

    if args.command == "plan-artifact-handoff":
        report = build_artifact_handoff_report(
            run_id=args.run_id,
            story_number=args.story_number,
            artifacts=_load_json_list(args.jobs_file, "artifact handoff jobs file"),
        )
        write_json_artifact_once(
            args.report_root,
            filename=f"{args.run_id}.json",
            payload=report,
        )
        print(_render_summary({"handoff_plans": report["summary"]["total"], **report["summary"]}))
        return 0

    if args.command == "write-artifact-handoff-summary":
        report = _load_json_object(args.report_file)
        story_number = str(report["story_number"])
        work_note = build_artifact_handoff_work_note(
            report=report,
            report_path=args.report_file,
        )
        if not args.apply:
            print(
                "handoff_summary_written=False "
                f"story_number={story_number} dry_run=True"
            )
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
        client = servicenow_client_from_env(args.env_file, transport=UrllibTransport())
        stories = client.fetch_stories(sysparm_query=f"number={story_number}", limit=1)
        if not stories:
            print(
                "handoff_summary_written=False "
                f"story_number={story_number} reason=story_not_found"
            )
            return 1
        client.update_story_fields(stories[0].sys_id, {"work_notes": work_note})
        print(f"handoff_summary_written=True story_number={story_number}")
        return 0

    if args.command == "attach-delivery-artifacts":
        report = _load_json_object(args.report_file)
        story_number = str(report["story_number"])
        try:
            delivery_jobs = delivery_attachment_jobs_from_report(report)
        except ValueError as exc:
            print(
                "delivery_attachments_planned=0 "
                f"delivery_attachments_applied=0 reason={exc}"
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
        client = servicenow_client_from_env(args.env_file, transport=UrllibTransport())
        stories = client.fetch_stories(sysparm_query=f"number={story_number}", limit=1)
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
                    "artifact_kind": delivery_job["artifact_kind"],
                    "artifact_path": delivery_job["artifact_path"],
                    "attachment_label": delivery_job["attachment_label"],
                    "attachment_sys_id": str(attachment.get("sys_id", "")),
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

    if args.command == "run-delivery-artifact-smoke":
        export_dir = args.artifact_root / "exports" / args.run_id
        export_dir.mkdir(parents=True, exist_ok=True)
        export_path = export_dir / f"{args.story_number}.xml"
        if export_path.exists():
            parser.error(f"delivery smoke artifact already exists: {export_path}")
        export_path.write_text(
            (
                f'<placeholder_update_set story_number="{args.story_number}" '
                'artifact_kind="update_set_xml">'
                "Attachment gate smoke only."
                "</placeholder_update_set>"
            ),
            encoding="utf-8",
        )
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

    if args.command == "plan-bootstrap-fields":
        client = servicenow_client_from_env(args.env_file, transport=UrllibTransport())
        bootstrap_plan = plan_bootstrap_fields(client.fetch_story_dictionary_fields())
        missing_fields = ",".join(bootstrap_plan.missing_fields)
        print(
            f"ready={bootstrap_plan.ready} table={bootstrap_plan.table} "
            f"missing_fields={missing_fields} "
            f"fields_to_create={len(bootstrap_plan.fields_to_create)} "
            f"form_layout_changes={len(bootstrap_plan.form_layout_changes)}"
        )
        return 0 if bootstrap_plan.ready else 1

    if args.command == "apply-bootstrap-fields":
        client = servicenow_client_from_env(args.env_file, transport=UrllibTransport())
        bootstrap_result = apply_bootstrap_fields(
            client,
            confirm_table=args.confirm_table,
            confirm_fields=args.confirm_fields,
        )
        audit_payload = bootstrap_result.model_dump(mode="json")
        audit_payload["run_id"] = args.run_id
        write_json_artifact_once(
            args.audit_root,
            filename=f"{args.run_id}.json",
            payload=audit_payload,
        )
        reasons = " ".join(f"reason={reason}" for reason in bootstrap_result.reasons)
        print(
            f"applied={bootstrap_result.applied} "
            f"created_fields={len(bootstrap_result.created_fields)} "
            f"form_layout_changes={len(bootstrap_result.form_layout_changes)} "
            f"{reasons}".strip()
        )
        return 0 if bootstrap_result.applied or not bootstrap_result.reasons else 1

    if args.command == "run-writeback-batch":
        client = servicenow_client_from_env(args.env_file, transport=UrllibTransport())
        requests = load_writeback_requests(
            args.jobs_file,
            apply=args.apply,
            actor_type=ActorType(args.actor_type),
            actor_id=args.actor_id,
            execution_id=args.execution_id,
            audit_root=args.audit_root,
        )
        batch = run_writeback_batch(client, requests)
        report_filename = f"{args.execution_id or 'writeback-batch'}.json"
        write_json_artifact_once(
            args.batch_report_root,
            filename=report_filename,
            payload=build_writeback_batch_report(
                batch,
                execution_id=args.execution_id,
                actor_id=args.actor_id,
            ),
        )
        print(_render_summary(batch.summary))
        return 0 if batch.summary["blocked"] == 0 else 1

    parser.print_help()
    return 0


def _load_sample_stories(path: Path) -> list[Story]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return [Story.model_validate(payload)]
    return [Story.model_validate(item) for item in payload]


def _load_stories_from_args(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
    command_name: str,
) -> list[Story]:
    sample_file = getattr(args, "sample_file", None)
    story_number = getattr(args, "story_number", None)
    if sample_file:
        return _load_sample_stories(sample_file)
    if story_number:
        client = servicenow_client_from_env(args.env_file, transport=UrllibTransport())
        return client.fetch_stories(
            sysparm_query=f"number={story_number}",
            limit=1,
        )
    parser.error(f"{command_name} requires --sample-file or --story-number")


def _load_json_object(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("provider response file must contain a JSON object")
    return payload


def _load_json_list(path: Path, description: str) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"{description} must contain a JSON list")
    if not all(isinstance(item, dict) for item in payload):
        raise ValueError(f"{description} entries must be JSON objects")
    return payload


def _load_implementation_candidate_jobs(path: Path) -> list[dict[str, Path]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("implementation candidate jobs file must contain a JSON list")

    jobs: list[dict[str, Path]] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("implementation candidate job must be a JSON object")
        sample_file = item.get("sample_file")
        provider_response_file = item.get("provider_response_file")
        if not isinstance(sample_file, str) or not isinstance(provider_response_file, str):
            raise ValueError(
                "implementation candidate job requires sample_file and "
                "provider_response_file"
            )
        jobs.append(
            {
                "sample_file": Path(sample_file),
                "provider_response_file": Path(provider_response_file),
            }
        )
    return jobs


def _content_type_for_artifact(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".xml":
        return "application/xml"
    if suffix == ".json":
        return "application/json"
    if suffix == ".zip":
        return "application/zip"
    return "application/octet-stream"


def _write_apply_lifecycle_manifest(
    *,
    client: WritebackClient,
    manifest_root: Path,
    run_id: str,
    story_number: str,
    build_reference: str,
    artifact_url: str | None,
    packet_path: Path | None,
    candidate_path: Path | None,
    candidate_batch_path: Path | None,
    writeback_result: WritebackExecutionResult,
) -> Path:
    if packet_path is None or candidate_path is None:
        raise ValueError("packet_path and candidate_path are required")
    verification = verify_writeback(
        client,
        story_number=story_number,
        build_reference=build_reference,
        artifact_url=artifact_url,
    )
    manifest_path = write_lifecycle_manifest(
        manifest_root,
        run_id=run_id,
        story_number=story_number,
        build_reference=build_reference,
        packet_path=packet_path,
        candidate_path=candidate_path,
        candidate_batch_path=candidate_batch_path,
        writeback_audit_path=writeback_result.audit_path,
        writeback={
            "allowed": writeback_result.allowed,
            "applied": writeback_result.applied,
            "idempotent": writeback_result.idempotent,
            "reasons": writeback_result.reasons or writeback_result.plan.reasons,
        },
        verification=verification.model_dump(mode="json"),
    )
    print(
        "lifecycle_manifest_written=True "
        f"story_number={story_number} path={manifest_path}"
    )
    return manifest_path


class StaticResponseProvider:
    def __init__(self, response: dict[str, object]) -> None:
        self._response = response

    def generate(self, payload: dict[str, object]) -> dict[str, object]:
        return self._response


def _default_policy() -> AllowlistPolicy:
    return AllowlistPolicy(
        story_types={StoryType.CONTENT_ONLY, StoryType.DICTIONARY_FORM},
        tables={"sp_instance", "sys_ui_message", "sys_dictionary", "sys_ui_form"},
        operations={"insert", "update"},
        max_points=3,
    )


def _default_implementation_provider_policy() -> ProviderPolicy:
    return ProviderPolicy(
        provider_id="now-assist-native",
        deployment_boundary="servicenow-federal-boundary",
        authorization_level="fedramp-aligned-evaluation",
        allowed_data_classes={DataClassification.PUBLIC},
        allowed_tasks={IMPLEMENTATION_PACKET_TASK},
        max_context_policy="implementation-packet-v1",
        retention_policy="customer-boundary",
        status=ProviderStatus.APPROVED,
    )


def _default_rags() -> SpecializedRags:
    return SpecializedRags.from_documents(
        [
            Document(
                domain=RagDomain.SERVICENOW_PLATFORM,
                source="local/servicenow-update-set-baseline",
                content=(
                    "Portal and dictionary form update sets capture configuration "
                    "updates for ServiceNow tables and fields."
                ),
                version="local",
            ),
            Document(
                domain=RagDomain.INSTANCE_METADATA,
                source="local/instance-sp-instance",
                content=(
                    "sp_instance stores portal widget instance text. rm_story field "
                    "changes use sys_dictionary and story form placement uses sys_ui_form."
                ),
                version="local",
            ),
            Document(
                domain=RagDomain.PROJECT_CONTEXT,
                source="local/project-scope",
                content=(
                    "Portal help text changes and low-risk rm_story dictionary/form "
                    "field changes are in scope."
                ),
                version="local",
            ),
            Document(
                domain=RagDomain.COMPLIANCE,
                source="local/compliance-model-use",
                content=(
                    "Portal and dictionary form candidates must be generated without "
                    "public AI endpoints."
                ),
                version="local",
            ),
        ]
    )


def _render_summary(summary: Mapping[str, object]) -> str:
    return " ".join(f"{key}={value}" for key, value in summary.items())


if __name__ == "__main__":
    raise SystemExit(main())
