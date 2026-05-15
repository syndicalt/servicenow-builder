from jedi_devproject.implementation_packet import (
    IMPLEMENTATION_PACKET_TASK,
    build_implementation_packet,
    generate_implementation_candidate,
    generate_implementation_update_set_candidate,
    generate_implementation_update_set_candidate_from_packet,
)
from jedi_devproject.instance_discovery import (
    DiscoveredField,
    DiscoveredFormElement,
    DiscoveredFormSection,
    InstanceDiscoveryContext,
    ServiceNowSurfaceContext,
    ServiceNowSurfaceContextBundle,
    ServiceNowSurfaceRecord,
)
from jedi_devproject.models import (
    CandidateStatus,
    DataClassification,
    ProviderPolicy,
    ProviderStatus,
    Story,
)
from jedi_devproject.providers import ModelResponseError
from jedi_devproject.rag import Document, RagDomain, SpecializedRags
from jedi_devproject.safety import AllowlistPolicy, StoryType


class RecordingImplementationProvider:
    def __init__(self, response: dict[str, object] | None = None) -> None:
        self.response = response or {
            "changes": [
                {
                    "table": "sys_dictionary",
                    "operation": "insert",
                    "fields": {
                        "name": "rm_story",
                        "element": "u_ai_review_notes",
                    },
                }
            ],
            "test_plan": ["Confirm field appears on Story form."],
            "rollback_notes": ["Remove field from form and dictionary."],
        }
        self.payloads: list[dict[str, object]] = []

    def generate(self, payload: dict[str, object]) -> dict[str, object]:
        self.payloads.append(payload)
        return self.response


class FailingImplementationProvider:
    def generate(self, payload: dict[str, object]) -> dict[str, object]:
        raise AssertionError("provider should not be called")


def _story() -> Story:
    return Story(
        sys_id="story-sys-id",
        number="STRY0010013",
        short_description="Add AI Review Notes field to Story form",
        description=(
            "Add u_ai_review_notes to rm_story and place it on the Story form for reviewer notes."
        ),
        acceptance_criteria=(
            "The AI Review Notes field is visible on the Story form and stores "
            "up to 8000 characters."
        ),
        story_points=3,
        priority=4,
        state="Ready",
        data_classification=DataClassification.PUBLIC,
        affected_tables=["sys_dictionary", "sys_ui_form"],
    )


def _rags() -> SpecializedRags:
    return SpecializedRags.from_documents(
        [
            Document(
                domain=RagDomain.SERVICENOW_PLATFORM,
                source="servicenow/docs/dictionary-form",
                content="Dictionary form field work uses sys_dictionary and sys_ui_form.",
                version="test",
            ),
            Document(
                domain=RagDomain.INSTANCE_METADATA,
                source="instance/rm_story",
                content="rm_story supports custom fields prefixed with u_.",
                version="test",
            ),
            Document(
                domain=RagDomain.PROJECT_CONTEXT,
                source="project/story-scope",
                content="AI review notes support human review of implementation candidates.",
                version="test",
            ),
            Document(
                domain=RagDomain.COMPLIANCE,
                source="compliance/model-boundary",
                content=(
                    "No public AI endpoint may receive story context. Incident field "
                    "stories stay inside the approved implementation boundary."
                ),
                version="test",
            ),
        ]
    )


def _policy() -> AllowlistPolicy:
    return AllowlistPolicy(
        story_types={StoryType.DICTIONARY_FORM},
        tables={"sys_dictionary", "sys_ui_form"},
        operations={"insert", "update"},
        max_points=3,
    )


def _provider_policy() -> ProviderPolicy:
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


def _discovery_context() -> InstanceDiscoveryContext:
    return InstanceDiscoveryContext(
        target_table="rm_story",
        table_label="Story",
        table_exists=True,
        supports_custom_fields=True,
        fields=[
            DiscoveredField(
                element="description",
                column_label="Description",
                internal_type="string",
                max_length=4000,
            )
        ],
        form_sections=[
            DiscoveredFormSection(
                sys_id="story-main-section",
                name="rm_story",
                elements=[
                    DiscoveredFormElement(
                        sys_id="description-element",
                        element="description",
                        position=2,
                    )
                ],
            )
        ],
        evidence=["sys_dictionary:rm_story", "sys_ui_section:rm_story"],
    )


def test_build_implementation_packet_contains_grounded_context_and_controls() -> None:
    packet = build_implementation_packet(
        story=_story(),
        policy=_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
    )

    assert packet.task == IMPLEMENTATION_PACKET_TASK
    assert packet.provider_id == "now-assist-native"
    assert packet.story.number == "STRY0010013"
    assert packet.allowed_tables == ["sys_dictionary", "sys_ui_form"]
    assert packet.allowed_operations == ["insert", "update"]
    assert packet.risk_score < 0.2
    assert packet.safety_decision == "automated_build"
    assert len(packet.retrieval_citations) >= 4
    assert "No public AI endpoint" in packet.context_sections["compliance"]
    assert "story-sys-id" not in packet.model_dump_json()


def test_build_implementation_packet_includes_discovered_instance_context() -> None:
    story = _story().model_copy(
        update={
            "number": "STRY0010001",
            "short_description": "Add a New Field to the Incident Form",
            "description": (
                "As an incident manager, I would like a new field added to the "
                "Incident form.\n\n- Field Name: Antics\n- Field Type: String\n"
                "- Length: 4000"
            ),
            "acceptance_criteria": "The field is placed below the Description field.",
            "affected_tables": [],
        }
    )
    discovery = InstanceDiscoveryContext(
        target_table="incident",
        table_label="Incident",
        table_exists=True,
        supports_custom_fields=True,
        fields=[
            DiscoveredField(
                element="description",
                column_label="Description",
                internal_type="string",
                max_length=4000,
            )
        ],
        form_sections=[
            DiscoveredFormSection(
                sys_id="incident-main-section",
                name="incident",
                elements=[
                    DiscoveredFormElement(
                        sys_id="description-element",
                        element="description",
                        position=2,
                    )
                ],
            )
        ],
        evidence=["sys_dictionary:incident.description"],
    )

    packet = build_implementation_packet(
        story=story,
        policy=_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
        discovery_context=discovery,
    )

    assert packet.safety_decision == "automated_build"
    assert packet.instance_context is not None
    assert packet.instance_context["target_table"] == "incident"
    assert packet.instance_context["fields"][0]["element"] == "description"
    assert packet.context_sufficiency["status"] == "sufficient"
    assert packet.context_sufficiency["score"] == 0.95
    assert packet.output_contract["must_use_discovered_instance_context"] is True


def test_build_implementation_packet_includes_surface_context_bundle() -> None:
    table_context = InstanceDiscoveryContext(
        target_table="incident",
        table_label="Incident",
        table_exists=True,
        supports_custom_fields=True,
        fields=[
            DiscoveredField(
                element="description",
                column_label="Description",
                internal_type="string",
                max_length=4000,
            )
        ],
        form_sections=[
            DiscoveredFormSection(
                sys_id="incident-main-section",
                name="incident",
                elements=[
                    DiscoveredFormElement(
                        sys_id="description-element",
                        element="description",
                        position=2,
                    )
                ],
            )
        ],
        evidence=["sys_dictionary:incident"],
    )
    bundle = ServiceNowSurfaceContextBundle(
        target_table="incident",
        required_surfaces=["table_schema", "form_layout", "business_rules"],
        table_context=table_context,
        surfaces=[
            ServiceNowSurfaceContext(
                surface="business_rules",
                source_table="sys_script",
                required=True,
                records=[
                    ServiceNowSurfaceRecord(
                        source_table="sys_script",
                        name="Incident State Guard",
                        active=True,
                        summary="before",
                    )
                ],
                evidence=["sys_script:incident"],
            )
        ],
        evidence=["sys_dictionary:incident", "sys_script:incident"],
    )

    packet = build_implementation_packet(
        story=_story().model_copy(
            update={
                "short_description": "Add incident field after checking business rules",
                "description": "Add a field to incident and account for business rules.",
            }
        ),
        policy=_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
        discovery_context=table_context,
        surface_context_bundle=bundle,
    )

    payload = packet.to_model_payload()

    assert packet.instance_context_bundle is not None
    assert packet.instance_context_bundle["target_table"] == "incident"
    assert packet.context_sufficiency["status"] == "sufficient"
    assert "sys_script:incident" in packet.context_sufficiency["evidence"]
    assert payload["instance_context_bundle"]["surfaces"][0]["surface"] == "business_rules"
    assert "business-rule-sys-id" not in packet.model_dump_json()


def test_build_implementation_packet_marks_missing_required_surface_insufficient() -> None:
    table_context = InstanceDiscoveryContext(
        target_table="incident",
        table_label="Incident",
        table_exists=True,
        supports_custom_fields=True,
        fields=[
            DiscoveredField(
                element="description",
                column_label="Description",
                internal_type="string",
            )
        ],
        form_sections=[
            DiscoveredFormSection(
                sys_id="incident-main-section",
                name="incident",
                elements=[
                    DiscoveredFormElement(
                        sys_id="description-element",
                        element="description",
                        position=2,
                    )
                ],
            )
        ],
        evidence=["sys_dictionary:incident"],
    )
    bundle = ServiceNowSurfaceContextBundle(
        target_table="incident",
        required_surfaces=["table_schema", "form_layout", "flows"],
        table_context=table_context,
        surfaces=[],
        missing_required_surfaces=["flows"],
        evidence=["sys_dictionary:incident"],
    )

    packet = build_implementation_packet(
        story=_story().model_copy(
            update={
                "short_description": "Update Incident Flow",
                "description": "Update the Incident Flow before adding a field.",
            }
        ),
        policy=_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
        discovery_context=table_context,
        surface_context_bundle=bundle,
    )

    assert packet.context_sufficiency["status"] == "insufficient"
    assert packet.context_sufficiency["missing_context"] == ["flows"]
    assert packet.to_model_payload()["controls"]["context_escalation"] == {
        "action": "manual_review",
        "should_retrieve": False,
        "should_call_model": False,
        "reasons": ["context_insufficient:flows"],
    }


def test_script_include_generation_does_not_require_form_layout_context() -> None:
    table_context = InstanceDiscoveryContext(
        target_table="global",
        table_label="Global",
        table_exists=False,
        supports_custom_fields=False,
        fields=[],
        form_sections=[],
        evidence=["sys_script_include:active"],
    )
    bundle = ServiceNowSurfaceContextBundle(
        target_table="global",
        required_surfaces=["script_includes"],
        table_context=table_context,
        surfaces=[
            ServiceNowSurfaceContext(
                surface="script_includes",
                source_table="sys_script_include",
                required=True,
                records=[
                    ServiceNowSurfaceRecord(
                        source_table="sys_script_include",
                        name="ExistingUtils",
                        active=True,
                        summary="Existing utility",
                    )
                ],
                evidence=["sys_script_include:active"],
            )
        ],
        evidence=["sys_script_include:active"],
    )
    story = _story().model_copy(
        update={
            "short_description": "Create JediIncidentUtils Script Include",
            "description": (
                "Create a Script Include named JediIncidentUtils in Global scope. "
                "Client callable: false. Expected server-side behavior: provide a "
                "normalizeCategory(category) function that returns the category lowercased. "
                "Tables read: none. Tables written: none. Fields read: none. Fields written: none."
            ),
            "acceptance_criteria": (
                "Calling normalizeCategory('Software') returns software. "
                "Rollback removes the generated Script Include."
            ),
            "affected_tables": [],
        }
    )

    packet = build_implementation_packet(
        story=story,
        policy=_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
        discovery_context=table_context,
        surface_context_bundle=bundle,
    )

    assert packet.safety_decision == "automated_build"
    assert packet.context_sufficiency["status"] == "sufficient"
    assert packet.context_sufficiency["missing_context"] == []
    assert packet.to_model_payload()["controls"]["context_escalation"]["should_call_model"] is True


def test_model_payload_compacts_surface_context_to_required_surfaces() -> None:
    table_context = InstanceDiscoveryContext(
        target_table="incident",
        table_label="Incident",
        table_exists=True,
        supports_custom_fields=True,
        fields=[
            DiscoveredField(
                element=f"u_field_{index}",
                column_label=f"Field {index}",
                internal_type="string",
            )
            for index in range(80)
        ],
        form_sections=[
            DiscoveredFormSection(
                sys_id="incident-main-section",
                name="incident",
                elements=[
                    DiscoveredFormElement(
                        sys_id=f"element-{index}",
                        element=f"field_{index}",
                        position=index,
                    )
                    for index in range(120)
                ],
            )
        ],
        evidence=["sys_dictionary:incident", "sys_ui_section:incident"],
    )
    bundle = ServiceNowSurfaceContextBundle(
        target_table="incident",
        required_surfaces=["table_schema", "form_layout"],
        table_context=table_context,
        surfaces=[
            ServiceNowSurfaceContext(
                surface="table_schema",
                source_table="sys_dictionary",
                required=True,
                records=[
                    ServiceNowSurfaceRecord(
                        source_table="sys_dictionary",
                        name=f"field_{index}",
                        active=True,
                        summary=f"Field {index}",
                        metadata={"internal_type": "string"},
                    )
                    for index in range(100)
                ],
                evidence=["sys_dictionary:incident"],
            ),
            ServiceNowSurfaceContext(
                surface="form_layout",
                source_table="sys_ui_section",
                required=True,
                records=[
                    ServiceNowSurfaceRecord(
                        source_table="sys_ui_section",
                        name=f"section_{index}",
                        active=True,
                        summary=f"Section {index}",
                    )
                    for index in range(20)
                ],
                evidence=["sys_ui_section:incident"],
            ),
            ServiceNowSurfaceContext(
                surface="ui_policies",
                source_table="sys_ui_policy",
                required=False,
                records=[
                    ServiceNowSurfaceRecord(
                        source_table="sys_ui_policy",
                        name=f"verbose policy {index}",
                        active=True,
                        summary="not required for this story",
                    )
                    for index in range(250)
                ],
                evidence=["sys_ui_policy:incident"],
            ),
        ],
        evidence=["sys_dictionary:incident", "sys_ui_section:incident"],
    )

    packet = build_implementation_packet(
        story=_story().model_copy(
            update={
                "short_description": "Add Incident Review Source field to Incident form",
                "description": (
                    "Add a custom string field to the Incident table. Field Name: "
                    "u_review_source. Column label: Review Source. Field Type: String. "
                    "Length: 120. Place the field on the default Incident form below Description."
                ),
                "acceptance_criteria": "The field appears on the default Incident form.",
                "affected_tables": [],
            }
        ),
        policy=_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
        discovery_context=table_context,
        surface_context_bundle=bundle,
    )

    model_bundle = packet.to_model_payload()["instance_context_bundle"]

    assert model_bundle["surfaces"][0]["surface"] == "table_schema"
    assert model_bundle["surfaces"][1]["surface"] == "form_layout"
    assert [surface["surface"] for surface in model_bundle["surfaces"]] == [
        "table_schema",
        "form_layout",
    ]
    assert len(model_bundle["surfaces"][0]["records"]) == 25
    assert len(model_bundle["table_context"]["fields"]) == 25
    assert len(model_bundle["table_context"]["form_sections"][0]["elements"]) == 25
    assert "verbose policy" not in str(model_bundle)
    assert packet.to_model_payload()["instance_context"] is None


def test_build_implementation_packet_marks_missing_instance_context_for_retrieval() -> None:
    packet = build_implementation_packet(
        story=_story(),
        policy=_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
    )

    assert packet.context_sufficiency == {
        "status": "needs_retrieval",
        "score": 0.35,
        "missing_context": ["live_instance_context"],
        "evidence": [],
    }
    assert packet.to_model_payload()["controls"]["context_sufficiency"]["status"] == (
        "needs_retrieval"
    )
    assert packet.to_model_payload()["controls"]["context_escalation"] == {
        "action": "retrieve_live_instance_context",
        "should_retrieve": True,
        "should_call_model": False,
        "reasons": ["live_instance_context_missing"],
    }


def test_implementation_packet_payload_is_model_ready_and_minimized() -> None:
    packet = build_implementation_packet(
        story=_story(),
        policy=_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
    )

    payload = packet.to_model_payload()

    assert payload["task"] == IMPLEMENTATION_PACKET_TASK
    assert payload["story"]["number"] == "STRY0010013"
    assert "sys_id" not in payload["story"]
    assert payload["controls"]["allowed_tables"] == ["sys_dictionary", "sys_ui_form"]
    assert payload["output_contract"]["must_return_manual_review_when_uncertain"] is True


def test_generate_implementation_candidate_sends_packet_to_approved_provider() -> None:
    provider = RecordingImplementationProvider()

    response = generate_implementation_candidate(
        story=_story(),
        policy=_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
        provider=provider,
    )

    assert response["changes"][0]["table"] == "sys_dictionary"
    assert provider.payloads[0]["task"] == IMPLEMENTATION_PACKET_TASK
    assert "story-sys-id" not in repr(provider.payloads[0])


def test_generate_implementation_candidate_rejects_missing_test_plan() -> None:
    provider = RecordingImplementationProvider(
        {
            "changes": [
                {
                    "table": "sys_dictionary",
                    "operation": "insert",
                    "fields": {
                        "name": "rm_story",
                        "element": "u_ai_review_notes",
                    },
                }
            ],
            "rollback_notes": ["Remove field from form and dictionary."],
        }
    )

    try:
        generate_implementation_candidate(
            story=_story(),
            policy=_policy(),
            provider_policy=_provider_policy(),
            rags=_rags(),
            provider=provider,
        )
    except ModelResponseError as exc:
        assert "test_plan must be a non-empty list" in str(exc)
    else:
        raise AssertionError("missing test_plan was accepted")


def test_generate_implementation_candidate_rejects_missing_rollback_notes() -> None:
    provider = RecordingImplementationProvider(
        {
            "changes": [
                {
                    "table": "sys_dictionary",
                    "operation": "insert",
                    "fields": {
                        "name": "rm_story",
                        "element": "u_ai_review_notes",
                    },
                }
            ],
            "test_plan": ["Confirm field appears on Story form."],
        }
    )

    try:
        generate_implementation_candidate(
            story=_story(),
            policy=_policy(),
            provider_policy=_provider_policy(),
            rags=_rags(),
            provider=provider,
        )
    except ModelResponseError as exc:
        assert "rollback_notes must be a non-empty list" in str(exc)
    else:
        raise AssertionError("missing rollback_notes was accepted")


def test_generate_implementation_update_set_candidate_maps_validated_model_response() -> None:
    provider = RecordingImplementationProvider()
    packet = build_implementation_packet(
        story=_story(),
        policy=_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
        discovery_context=_discovery_context(),
    )

    candidate = generate_implementation_update_set_candidate_from_packet(
        packet=packet,
        policy=_policy(),
        provider=provider,
    )

    assert candidate.story_number == "STRY0010013"
    assert candidate.status is CandidateStatus.READY_FOR_REVIEW
    assert candidate.eligibility_decision == "eligible"
    assert candidate.changes[0].table == "sys_dictionary"
    assert candidate.retrieval_citations
    assert candidate.artifact_hash
    assert "Confirm field appears" in candidate.reviewer_notes[0]
    assert "Rollback:" in candidate.reviewer_notes[-1]
    assert "story-sys-id" not in candidate.model_dump_json()


def test_generate_implementation_update_set_candidate_treats_placeholder_sys_id_as_absent() -> None:
    provider = RecordingImplementationProvider(
        {
            "changes": [
                {
                    "table": "sys_ui_form",
                    "operation": "update",
                    "fields": {
                        "view_name": "Default",
                        "field_name": "u_ai_review_notes",
                    },
                    "sys_id": "[FORM_SYS_ID_HERE]",
                }
            ],
            "test_plan": ["Confirm field appears on Story form."],
            "rollback_notes": ["Remove field from form."],
        }
    )
    packet = build_implementation_packet(
        story=_story(),
        policy=_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
        discovery_context=_discovery_context(),
    )

    candidate = generate_implementation_update_set_candidate_from_packet(
        packet=packet,
        policy=_policy(),
        provider=provider,
    )

    assert candidate.changes[0].sys_id is None


def test_generate_implementation_update_set_candidate_skips_provider_for_manual_review() -> None:
    manual_review_story = _story().model_copy(update={"story_points": 8})

    candidate = generate_implementation_update_set_candidate(
        story=manual_review_story,
        policy=_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
        provider=FailingImplementationProvider(),
    )

    assert candidate.status is CandidateStatus.MANUAL_BUILD
    assert candidate.eligibility_decision == "manual_review"
    assert candidate.changes == []
    assert "deterministic safety or context gate" in candidate.reviewer_notes[0]
