"""CLI command implementations for pipeline runs and implementation candidates."""

from __future__ import annotations

import argparse
from pathlib import Path

from jedi_devproject.artifacts import (
    write_candidate_artifact,
    write_json_artifact_once,
    write_lifecycle_manifest,
)
from jedi_devproject.cli_io import (
    load_json_list,
    load_json_object,
    load_json_payload,
    render_summary,
)
from jedi_devproject.exception_diagnostics import exception_diagnostic_message
from jedi_devproject.implementation_packet import (
    IMPLEMENTATION_PACKET_TASK,
    build_implementation_packet,
    generate_implementation_update_set_candidate_from_packet,
)
from jedi_devproject.instance_discovery import (
    DiscoveredField,
    DiscoveredFormElement,
    DiscoveredFormSection,
    InstanceDiscoveryContext,
)
from jedi_devproject.models import (
    DataClassification,
    ProviderPolicy,
    ProviderStatus,
    Story,
    UpdateSetCandidate,
)
from jedi_devproject.pipeline import PipelineInputs, run_pipeline
from jedi_devproject.rag import Document, RagDomain, SpecializedRags
from jedi_devproject.safety import AllowlistPolicy, StoryType
from jedi_devproject.servicenow import ServiceNowClient, UrllibTransport
from jedi_devproject.writeback_orchestration import (
    WritebackExecutionRequest,
    execute_writeback,
)

CLI_PIPELINE_STORY_LOOKUP_RESULT_UNSAFE_REASON = "story_lookup_result_unsafe"


def _client_from_env(env_file: Path) -> ServiceNowClient:
    # Resolved through the CLI facade so patches against
    # jedi_devproject.cli.servicenow_client_from_env keep intercepting it.
    from jedi_devproject import cli

    return cli.servicenow_client_from_env(env_file, transport=UrllibTransport())


def run_local_command(args: argparse.Namespace) -> int:
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
    print(render_summary(result.summary))
    return 0


def run_pdi_command(args: argparse.Namespace) -> int:
    client = _client_from_env(args.env_file)
    try:
        if args.sysparm_query:
            stories = _pipeline_story_lookup_results(
                client.fetch_stories(sysparm_query=args.sysparm_query, limit=args.limit)
            )
        elif args.project_sys_id:
            stories = _pipeline_story_lookup_results(
                client.fetch_ready_stories(
                    project_sys_id=args.project_sys_id,
                    limit=args.limit,
                )
            )
        else:
            stories = _pipeline_story_lookup_results(client.fetch_stories(limit=args.limit))
    except ValueError:
        print(
            "stories_processed=0 generated_candidates=0 "
            f"reason={CLI_PIPELINE_STORY_LOOKUP_RESULT_UNSAFE_REASON}"
        )
        return 1
    result = run_pipeline(
        PipelineInputs(
            stories=stories,
            policy=_default_policy(),
            rags=_default_rags(),
            artifact_root=args.artifact_root,
            run_id=args.run_id,
        )
    )
    print(render_summary(result.summary))
    return 0


def build_implementation_packet_command(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> int:
    try:
        stories = _load_stories_from_args(args, parser, "build-implementation-packet")
    except ValueError as exc:
        if str(exc) != CLI_PIPELINE_STORY_LOOKUP_RESULT_UNSAFE_REASON:
            raise
        print(
            "implementation_packets=0 "
            f"reason={CLI_PIPELINE_STORY_LOOKUP_RESULT_UNSAFE_REASON}"
        )
        return 1
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


def build_implementation_candidate_command(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> int:
    try:
        stories = _load_stories_from_args(args, parser, "build-implementation-candidate")
    except ValueError as exc:
        if str(exc) != CLI_PIPELINE_STORY_LOOKUP_RESULT_UNSAFE_REASON:
            raise
        print(
            "implementation_candidates=0 "
            f"reason={CLI_PIPELINE_STORY_LOOKUP_RESULT_UNSAFE_REASON}"
        )
        return 1
    if not stories:
        print("implementation_candidates=0 reason=no_stories_found")
        return 1
    provider = StaticResponseProvider(load_json_object(args.provider_response_file))
    for story in stories:
        candidate = _build_offline_implementation_candidate(story=story, provider=provider)
        write_candidate_artifact(
            args.artifact_root,
            run_id=args.run_id,
            candidate=candidate,
        )
    print(f"implementation_candidates={len(stories)} run_id={args.run_id}")
    return 0


def run_implementation_candidates_command(args: argparse.Namespace) -> int:
    jobs = _load_implementation_candidate_jobs(args.jobs_file)
    if not jobs:
        print("total=0 built=0 blocked=0 reason=no_jobs")
        return 1
    built = 0
    blocked = 0
    outcomes: list[dict[str, object]] = []
    for job in jobs:
        stories = _load_sample_stories(job["sample_file"])
        provider = StaticResponseProvider(load_json_object(job["provider_response_file"]))
        for story in stories:
            try:
                candidate = _build_offline_implementation_candidate(
                    story=story,
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
                        "reason": exception_diagnostic_message(
                            exc,
                            fallback_subject="CLI batch",
                        ),
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
    print(render_summary(summary))
    return 0 if blocked == 0 else 1


def run_lifecycle_smoke_command(args: argparse.Namespace) -> int:
    client = _client_from_env(args.env_file)
    try:
        stories = _pipeline_story_lookup_results(
            client.fetch_stories(
                sysparm_query=f"number={args.story_number}",
                limit=1,
            )
        )
    except ValueError:
        print(
            "packet_built=0 candidate_built=0 "
            "writeback_allowed=False writeback_applied=False "
            f"reason={CLI_PIPELINE_STORY_LOOKUP_RESULT_UNSAFE_REASON}"
        )
        return 1
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
        discovery_context=_offline_discovery_context(story),
    )
    packet_root = args.artifact_root / "implementation-packets" / args.run_id
    write_json_artifact_once(
        packet_root,
        filename=f"{story.number}.json",
        payload=packet.to_model_payload(),
    )

    candidate = _build_offline_implementation_candidate(
        story=story,
        provider=StaticResponseProvider(load_json_object(args.provider_response_file)),
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


def _load_sample_stories(path: Path) -> list[Story]:
    payload = load_json_payload(path)
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
        client = _client_from_env(args.env_file)
        return _pipeline_story_lookup_results(
            client.fetch_stories(
                sysparm_query=f"number={story_number}",
                limit=1,
            )
        )
    parser.error(f"{command_name} requires --sample-file or --story-number")


def _pipeline_story_lookup_results(stories: object) -> list[Story]:
    if type(stories) is not list:
        raise ValueError(CLI_PIPELINE_STORY_LOOKUP_RESULT_UNSAFE_REASON)
    for story in stories:
        if type(story) is not Story:
            raise ValueError(CLI_PIPELINE_STORY_LOOKUP_RESULT_UNSAFE_REASON)
    return stories


def _load_implementation_candidate_jobs(path: Path) -> list[dict[str, Path]]:
    payload = load_json_list(path, "implementation candidate jobs file")

    jobs: list[dict[str, Path]] = []
    for item in payload:
        sample_file = item.get("sample_file")
        provider_response_file = item.get("provider_response_file")
        if not isinstance(sample_file, str) or not isinstance(provider_response_file, str):
            raise ValueError(
                "implementation candidate job requires sample_file and provider_response_file"
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


def _build_offline_implementation_candidate(
    *,
    story: Story,
    provider: StaticResponseProvider,
) -> UpdateSetCandidate:
    policy = _default_policy()
    packet = build_implementation_packet(
        story=story,
        policy=policy,
        provider_policy=_default_implementation_provider_policy(),
        rags=_default_rags(),
        discovery_context=_offline_discovery_context(story),
    )
    return generate_implementation_update_set_candidate_from_packet(
        packet=packet,
        policy=policy,
        provider=provider,
    )


def _offline_discovery_context(story: Story) -> InstanceDiscoveryContext:
    target_table = str(story.additional_context.get("target_table") or "rm_story")
    anchor = str(story.additional_context.get("placement_anchor") or "description")
    return InstanceDiscoveryContext(
        target_table=target_table,
        table_label=target_table.replace("_", " ").title(),
        table_exists=True,
        supports_custom_fields=True,
        fields=[
            DiscoveredField(
                element=anchor,
                column_label=anchor.replace("_", " ").title(),
                internal_type="string",
                max_length=4000,
            )
        ],
        form_sections=[
            DiscoveredFormSection(
                sys_id="offline-section-redacted",
                name=target_table,
                elements=[
                    DiscoveredFormElement(
                        sys_id="offline-element-redacted",
                        element=anchor,
                        position=1,
                    )
                ],
            )
        ],
        evidence=[
            f"offline_reviewed_context:{target_table}",
            f"offline_reviewed_anchor:{anchor}",
        ],
    )


def _default_policy() -> AllowlistPolicy:
    return AllowlistPolicy(
        story_types={StoryType.CONTENT_ONLY, StoryType.DICTIONARY_FORM},
        tables={
            "sp_instance",
            "sys_ui_message",
            "sys_dictionary",
            "sys_ui_form",
            "sc_cat_item",
            "item_option_new",
            "sc_cat_item_category",
            "m2m_connected_content",
        },
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
