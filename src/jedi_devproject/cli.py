from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path

from jedi_devproject import __version__
from jedi_devproject.artifacts import write_candidate_artifact, write_json_artifact_once
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
    WritebackExecutionRequest,
    build_writeback_batch_report,
    evaluate_writeback_capability,
    execute_writeback,
    load_writeback_requests,
    run_writeback_batch,
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
    check_writeback = subparsers.add_parser(
        "check-writeback-capability",
        help="Check whether the ServiceNow instance supports structured writeback.",
    )
    check_writeback.add_argument("--env-file", type=Path, default=Path(".env"))
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

    if args.command == "plan-writeback":
        client = servicenow_client_from_env(args.env_file, transport=UrllibTransport())
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
