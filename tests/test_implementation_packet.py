import math

import pytest

from jedi_devproject.builder_maturity import MaturityEvidence
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
from jedi_devproject.packet_intent_changes import (
    _catalog_item_changes_from_normalized_intent,
    _record_producer_changes_from_normalized_intent,
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


class StubMaturityProvider:
    def __init__(self, evidence_by_surface: dict[str, MaturityEvidence]) -> None:
        self.evidence_by_surface = evidence_by_surface
        self.requested: list[str] = []

    def maturity_evidence_for_surface(self, surface: str) -> MaturityEvidence:
        self.requested.append(surface)
        return self.evidence_by_surface.get(
            surface,
            MaturityEvidence(surface=surface, samples=0, successes=0, failures=0),
        )


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
                    "stories and Catalog Item requests stay inside the approved "
                    "implementation boundary."
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


def _catalog_policy() -> AllowlistPolicy:
    return AllowlistPolicy(
        story_types={StoryType.DICTIONARY_FORM},
        tables={
            "sc_cat_item",
            "item_option_new",
            "sc_cat_item_category",
            "m2m_connected_content",
        },
        operations={"insert", "update"},
        max_points=3,
    )


def _ui_policy_policy() -> AllowlistPolicy:
    return AllowlistPolicy(
        story_types={StoryType.DICTIONARY_FORM},
        tables={"sys_ui_policy", "sys_ui_policy_action"},
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


def _ui_policy_story() -> Story:
    return Story(
        sys_id="ui-policy-story-sys-id",
        number="STRY0010123",
        short_description="Create UI Policy for Software Incident assignment group",
        description=(
            "Create a UI Policy on the incident table. Condition: category=software. "
            "Fields read: category. Fields affected: assignment_group. "
            "Expected behavior: make assignment_group mandatory and visible. "
            "Reverse if false: true."
        ),
        acceptance_criteria=(
            "Given an Incident with category Software, when the form loads, then "
            "Assignment group is mandatory and visible. Given category is not Software, "
            "when the condition is false, then the policy must reverse."
        ),
        story_points=3,
        priority=4,
        state="Ready",
        data_classification=DataClassification.PUBLIC,
        affected_tables=["sys_ui_policy", "sys_ui_policy_action"],
    )


def _ui_policy_context_bundle() -> ServiceNowSurfaceContextBundle:
    table_context = InstanceDiscoveryContext(
        target_table="incident",
        table_label="Incident",
        table_exists=True,
        supports_custom_fields=True,
        fields=[
            DiscoveredField(
                element="category",
                column_label="Category",
                internal_type="choice",
            ),
            DiscoveredField(
                element="assignment_group",
                column_label="Assignment group",
                internal_type="reference",
            ),
        ],
        form_sections=[
            DiscoveredFormSection(
                sys_id="incident-main-section",
                name="incident",
                elements=[
                    DiscoveredFormElement(
                        sys_id="category-element",
                        element="category",
                        position=2,
                    ),
                    DiscoveredFormElement(
                        sys_id="assignment-group-element",
                        element="assignment_group",
                        position=10,
                    ),
                ],
            )
        ],
        evidence=["sys_dictionary:incident", "sys_ui_section:incident"],
    )
    return ServiceNowSurfaceContextBundle(
        target_table="incident",
        required_surfaces=["table_schema", "form_layout", "ui_policies"],
        table_context=table_context,
        surfaces=[
            ServiceNowSurfaceContext(
                surface="table_schema",
                source_table="sys_dictionary",
                required=True,
                records=[
                    ServiceNowSurfaceRecord(
                        source_table="sys_dictionary",
                        name="category",
                        active=True,
                        summary="Category",
                        metadata={"internal_type": "choice"},
                    ),
                    ServiceNowSurfaceRecord(
                        source_table="sys_dictionary",
                        name="assignment_group",
                        active=True,
                        summary="Assignment group",
                        metadata={"internal_type": "reference"},
                    ),
                ],
                evidence=["sys_dictionary:incident"],
                confidence=1.0,
            ),
            ServiceNowSurfaceContext(
                surface="form_layout",
                source_table="sys_ui_section",
                required=True,
                records=[
                    ServiceNowSurfaceRecord(
                        source_table="sys_ui_section",
                        name="incident",
                        active=True,
                        summary="",
                    )
                ],
                evidence=["sys_ui_section:incident"],
                confidence=1.0,
            ),
            ServiceNowSurfaceContext(
                surface="ui_policies",
                source_table="sys_ui_policy",
                required=True,
                records=[],
                evidence=["sys_ui_policy:incident"],
                confidence=0.0,
            ),
        ],
        evidence=["sys_dictionary:incident", "sys_ui_section:incident", "sys_ui_policy:incident"],
    )


def _catalog_story() -> Story:
    return Story(
        sys_id="catalog-story-sys-id",
        number="STRY0010025",
        short_description="JEDI UAT: Request Temporary Visitor Badge Catalog Item",
        description=(
            "Target artifact type: Catalog Item\n"
            "Artifact name: Request Temporary Visitor Badge\n"
            "Short description: Request a temporary building access badge for a visitor.\n"
            "Catalog: Service Catalog\n"
            "Category: Services\n"
            "Taxonomy: Employee\n"
            "Employee Center topic: Technology services / Software / Access issues\n"
            "Variables: visitor_name|Visitor name|single_line_text|mandatory=true|order=100; "
            "business_justification|Business justification|multi_line_text|"
            "mandatory=true|order=200; "
            "sponsor|Sponsor|reference|sys_user|active=true|mandatory=true|order=300\n"
            "Forbidden behavior: Do not create flows, approvals, catalog client scripts, "
            "catalog UI policies, user criteria, pricing, or integrations."
        ),
        acceptance_criteria="Delivery is a retrieved Update Set ready for preview and commit.",
        story_points=3,
        priority=4,
        state="Work in Progress",
        data_classification=DataClassification.PUBLIC,
    )


def _catalog_context_bundle() -> ServiceNowSurfaceContextBundle:
    table_context = InstanceDiscoveryContext(
        target_table="sc_cat_item",
        table_label="Catalog Item",
        table_exists=True,
        supports_custom_fields=True,
        fields=[],
        form_sections=[],
        evidence=["sys_db_object:sc_cat_item"],
    )
    return ServiceNowSurfaceContextBundle(
        target_table="sc_cat_item",
        required_surfaces=[
            "catalog_definitions",
            "catalog_categories",
            "employee_center_topics",
            "employee_center_connected_content",
        ],
        table_context=table_context,
        surfaces=[
            ServiceNowSurfaceContext(
                surface="catalog_definitions",
                source_table="sc_catalog",
                required=True,
                records=[
                    ServiceNowSurfaceRecord(
                        source_table="sc_catalog",
                        name="Service Catalog",
                        active=True,
                    )
                ],
                evidence=["sc_catalog:active"],
                confidence=0.95,
            ),
            ServiceNowSurfaceContext(
                surface="catalog_categories",
                source_table="sc_category",
                required=True,
                records=[
                    ServiceNowSurfaceRecord(
                        source_table="sc_category",
                        name="Services",
                        active=True,
                    )
                ],
                evidence=["sc_category:active"],
                confidence=0.95,
            ),
            ServiceNowSurfaceContext(
                surface="employee_center_topics",
                source_table="topic",
                required=True,
                records=[
                    ServiceNowSurfaceRecord(
                        source_table="topic",
                        name="Technology services / Software / Access issues",
                        active=True,
                    )
                ],
                evidence=["topic:active"],
                confidence=0.95,
            ),
            ServiceNowSurfaceContext(
                surface="employee_center_connected_content",
                source_table="taxonomy_content_configuration",
                required=True,
                records=[
                    ServiceNowSurfaceRecord(
                        source_table="taxonomy_content_configuration",
                        name="Catalog Item",
                        active=True,
                    )
                ],
                evidence=["taxonomy_content_configuration:active"],
                confidence=0.95,
            ),
        ],
        evidence=["sc_catalog:active", "topic:active"],
    )


def _form_section_story() -> Story:
    return Story(
        sys_id="form-section-story-sys-id",
        number="STRY0010011",
        short_description="DMND: Hide Demand form tabs",
        description=(
            "Target artifact type: Form Section Removal\n"
            "Target table: dmn_demand\n"
            "View: Default view\n"
            "Sections: Assessment, Financials\n"
            "Actions: Hide the Assessment and Financials tabs."
        ),
        acceptance_criteria="The Demand form does not display the Assessment and Financials tabs.",
        story_points=3,
        priority=4,
        state="Work in Progress",
        data_classification=DataClassification.PUBLIC,
    )


def _form_section_context_bundle() -> ServiceNowSurfaceContextBundle:
    table_context = InstanceDiscoveryContext(
        target_table="dmn_demand",
        table_label="Demand",
        table_exists=True,
        supports_custom_fields=True,
        fields=[],
        form_sections=[
            DiscoveredFormSection(
                sys_id="demand-main-section",
                name="dmn_demand",
                elements=[],
            ),
            DiscoveredFormSection(
                sys_id="demand-assessment-section",
                name="dmn_demand",
                caption="Assessment Data",
                view_name="Default view",
                elements=[],
            ),
            DiscoveredFormSection(
                sys_id="demand-financials-section",
                name="dmn_demand",
                caption="Financials",
                view_name="Default view",
                elements=[],
            ),
        ],
        evidence=["sys_ui_section:dmn_demand"],
    )
    return ServiceNowSurfaceContextBundle(
        target_table="dmn_demand",
        required_surfaces=["form_sections", "form_layout"],
        table_context=table_context,
        surfaces=[
            ServiceNowSurfaceContext(
                surface="form_sections",
                source_table="sys_ui_section",
                required=True,
                records=[
                    ServiceNowSurfaceRecord(
                        source_table="sys_ui_section",
                        name="Assessment Data",
                        active=True,
                        summary="Demand Assessment Data section",
                    )
                ],
                evidence=["sys_ui_section:dmn_demand"],
            ),
            ServiceNowSurfaceContext(
                surface="form_layout",
                source_table="sys_ui_element",
                required=True,
                records=[],
                evidence=["sys_ui_element:dmn_demand"],
            ),
        ],
        missing_required_surfaces=[],
        evidence=["sys_ui_section:dmn_demand", "sys_ui_element:dmn_demand"],
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


def test_model_payload_includes_structured_context_dossier_with_xml_shape_references() -> None:
    bundle = _form_section_context_bundle()

    packet = build_implementation_packet(
        story=_form_section_story(),
        policy=AllowlistPolicy(
            story_types={StoryType.DICTIONARY_FORM},
            tables={"sys_ui_section"},
            operations={"delete"},
            max_points=3,
        ),
        provider_policy=_provider_policy(),
        rags=_rags(),
        discovery_context=bundle.table_context,
        surface_context_bundle=bundle,
    )

    payload = packet.to_model_payload()
    dossier = payload["context_dossier"]

    assert dossier["story"]["number"] == "STRY0010011"
    assert dossier["target"]["table"] == "dmn_demand"
    assert dossier["context_sufficiency"]["status"] == "sufficient"
    assert dossier["xml_shape_references"] == [
        {
            "surface": "form_layout",
            "record_type": "sys_ui_section",
            "operation": "delete",
            "required_records": ["sys_ui_section", "sys_ui_element"],
            "important_fields": [
                "sys_id",
                "caption",
                "name",
                "view",
                "sys_update_name",
            ],
            "notes": (
                "Reference only. Use this to reason about structured changes; "
                "do not output raw XML."
            ),
        }
    ]
    assert payload["output_contract"]["format"] == "structured_candidate_change_only"
    assert payload["output_contract"]["must_not_output_raw_xml"] is True
    assert payload["output_contract"]["xml_shape_references_are_read_only"] is True
    assert "<record_update" not in str(payload)
    assert "<sys_update_xml" not in str(payload)
    assert "payload><![CDATA" not in str(payload)


def test_packet_uses_typed_intent_for_structured_client_script_story() -> None:
    story = _story().model_copy(
        update={
            "number": "STRY0010022",
            "short_description": "JEDI UAT: Warn when Software Incident has no CI",
            "description": (
                "Target artifact type: Client Script\n"
                "Target table: incident\n"
                "Artifact name: JEDI UAT Software CI Reminder\n"
                "Client script type: onChange\n"
                "Target field: category\n"
                "Condition: category changes to software and cmdb_ci is empty\n"
                "Actions: Show an informational message reminding the fulfiller "
                "to select the affected Configuration item.\n"
                "Fields read: category, cmdb_ci\n"
                "Fields written / affected: none\n"
                "Forbidden behavior: Do not use GlideAjax, document APIs, window "
                "APIs, browser storage, external calls, credentials, form submit, "
                "or unrelated field writes."
            ),
            "acceptance_criteria": "Delivery is a retrieved Update Set.",
            "affected_tables": [],
        }
    )
    table_context = InstanceDiscoveryContext(
        target_table="incident",
        table_label="Incident",
        table_exists=True,
        supports_custom_fields=True,
        fields=[
            DiscoveredField(element="category", column_label="Category", internal_type="choice"),
            DiscoveredField(
                element="cmdb_ci",
                column_label="Configuration item",
                internal_type="reference",
            ),
        ],
        form_sections=[],
        evidence=["sys_dictionary:incident"],
    )
    bundle = ServiceNowSurfaceContextBundle(
        target_table="incident",
        required_surfaces=["table_schema", "client_scripts"],
        table_context=table_context,
        surfaces=[],
        missing_required_surfaces=[],
        evidence=["sys_dictionary:incident", "sys_script_client:incident"],
    )

    packet = build_implementation_packet(
        story=story,
        policy=_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
        discovery_context=table_context,
        surface_context_bundle=bundle,
    )

    assert packet.normalized_intent is not None
    assert packet.normalized_intent["intent_type"] == "client_script"
    assert packet.normalized_intent["fields_read"] == ["category", "cmdb_ci"]
    assert packet.normalized_intent["fields_written"] == []
    assert packet.capability_assessment["required_instance_context"] == [
        "table_schema",
        "client_scripts",
    ]
    assert "cmdb_discovery_maps" not in packet.context_sufficiency["missing_context"]


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


def test_generate_implementation_update_set_candidate_rejects_empty_model_changes() -> None:
    provider = RecordingImplementationProvider(
        {
            "changes": [],
            "test_plan": ["Validate requested Script Include."],
            "rollback_notes": ["No generated platform changes."],
        }
    )
    packet = build_implementation_packet(
        story=_story(),
        policy=_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
        discovery_context=_discovery_context(),
    )

    try:
        generate_implementation_update_set_candidate_from_packet(
            packet=packet,
            policy=_policy(),
            provider=provider,
        )
    except ModelResponseError as exc:
        assert "changes must be a non-empty list" in str(exc)
    else:
        raise AssertionError("empty automated model changes were accepted")


def test_catalog_candidate_reconciles_variables_from_normalized_intent() -> None:
    provider = RecordingImplementationProvider(
        {
            "changes": [
                {
                    "table": "sc_cat_item",
                    "operation": "insert",
                    "fields": {
                        "name": "Request Temporary Visitor Badge",
                        "short_description": (
                            "Request a temporary building access badge for a visitor."
                        ),
                        "catalog": "Service Catalog",
                        "category": "Services",
                        "taxonomy": "Employee",
                        "employee_center_topic": (
                            "Technology services / Software / Access issues"
                        ),
                    },
                    "sys_id": None,
                    "rationale": "Create the catalog item.",
                },
                {
                    "table": "item_option_new",
                    "operation": "insert",
                    "fields": {
                        "name": "visitor_name",
                        "label": "",
                        "type": "single_line_text",
                    },
                    "sys_id": None,
                    "rationale": "Collect the visitor name.",
                },
            ],
            "test_plan": ["Preview the retrieved Update Set."],
            "rollback_notes": ["Back out the retrieved Update Set."],
        }
    )
    bundle = _catalog_context_bundle()
    packet = build_implementation_packet(
        story=_catalog_story(),
        policy=_catalog_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
        discovery_context=bundle.table_context,
        surface_context_bundle=bundle,
    )

    candidate = generate_implementation_update_set_candidate_from_packet(
        packet=packet,
        policy=_catalog_policy(),
        provider=provider,
    )

    variable_changes = [change for change in candidate.changes if change.table == "item_option_new"]
    assert [change.fields["question_text"] for change in variable_changes] == [
        "Visitor name",
        "Business justification",
        "Sponsor",
    ]
    assert variable_changes[2].fields["reference"] == "sys_user"
    assert variable_changes[2].fields["reference_qualifier"] == "active=true"
    assert {change.table for change in candidate.changes} == {
        "sc_cat_item",
        "item_option_new",
        "sc_cat_item_category",
        "m2m_connected_content",
    }
    sc_cat_item_change = next(
        change for change in candidate.changes if change.table == "sc_cat_item"
    )
    assert "variable_sets" not in sc_cat_item_change.fields
    assert "variable_groups" not in sc_cat_item_change.fields


def _catalog_normalized_intent(**overrides: object) -> dict[str, object]:
    intent: dict[str, object] = {
        "artifact_name": "Request Temporary Badge",
        "catalog_item_short_description": "Request a temporary access badge.",
        "catalog_name": "Service Catalog",
        "category_name": "Services",
        "taxonomy_name": "Employee",
        "employee_center_topic": "Technology services / Software / Access issues",
        "catalog_variables": [
            {"name": "visitor_name", "label": "Visitor name", "type": "single_line_text"},
            {"name": "start_date", "label": "Start date", "type": "date"},
            {"name": "end_date", "label": "End date", "type": "date"},
        ],
    }
    intent.update(overrides)
    return intent


def test_catalog_changes_carry_variable_sets_and_groups_from_normalized_intent() -> None:
    changes = _catalog_item_changes_from_normalized_intent(
        _catalog_normalized_intent(
            catalog_variable_sets=["Common Visitor Questions"],
            catalog_variable_groups=[
                {"title": "Schedule", "variables": ["start_date", "end_date"]}
            ],
        )
    )

    sc_cat_item_fields = changes[0]["fields"]
    assert sc_cat_item_fields["variable_sets"] == ["Common Visitor Questions"]
    assert sc_cat_item_fields["variable_groups"] == [
        {"title": "Schedule", "variables": ["start_date", "end_date"]}
    ]


def test_catalog_changes_reject_variable_set_creation() -> None:
    with pytest.raises(ModelResponseError, match="must not create variable sets"):
        _catalog_item_changes_from_normalized_intent(
            _catalog_normalized_intent(catalog_variable_set_creation=True)
        )


def test_catalog_changes_reject_group_referencing_unknown_variable() -> None:
    with pytest.raises(ModelResponseError, match="references unknown variable: badge_color"):
        _catalog_item_changes_from_normalized_intent(
            _catalog_normalized_intent(
                catalog_variable_groups=[{"title": "Schedule", "variables": ["badge_color"]}]
            )
        )


def test_catalog_changes_reject_non_declarative_reference_qualifier() -> None:
    with pytest.raises(ModelResponseError, match="reference qualifier rejected"):
        _catalog_item_changes_from_normalized_intent(
            _catalog_normalized_intent(
                catalog_variables=[
                    {
                        "name": "sponsor",
                        "label": "Sponsor",
                        "type": "reference",
                        "reference_table": "sys_user",
                        "reference_qualifier": "javascript:gs.getUser()",
                    }
                ]
            )
        )


def test_catalog_changes_carry_fulfillment_flow_from_normalized_intent() -> None:
    changes = _catalog_item_changes_from_normalized_intent(
        _catalog_normalized_intent(
            fulfillment_flow=(
                "Attach the existing flow Badge Access Fulfillment as the fulfillment flow"
            ),
            fulfillment_flow_name="Badge Access Fulfillment",
            fulfillment_flow_attachment_requested=True,
        )
    )

    assert changes[0]["fields"]["fulfillment_flow"] == "Badge Access Fulfillment"
    assert {change["table"] for change in changes} == {
        "sc_cat_item",
        "item_option_new",
        "sc_cat_item_category",
        "m2m_connected_content",
    }
    assert all(
        "fulfillment_flow" not in change["fields"] for change in changes[1:]
    )


def test_catalog_changes_without_fulfillment_flow_carry_no_flow_field() -> None:
    changes = _catalog_item_changes_from_normalized_intent(_catalog_normalized_intent())

    assert "fulfillment_flow" not in changes[0]["fields"]


def test_catalog_changes_reject_fulfillment_flow_creation_or_modification() -> None:
    with pytest.raises(ModelResponseError, match="must not create or modify fulfillment flows"):
        _catalog_item_changes_from_normalized_intent(
            _catalog_normalized_intent(fulfillment_flow="Create a new Badge Fulfillment flow")
        )


def test_catalog_changes_reject_flow_attachment_without_a_name() -> None:
    with pytest.raises(ModelResponseError, match="requires a flow name"):
        _catalog_item_changes_from_normalized_intent(
            _catalog_normalized_intent(
                fulfillment_flow="Attach an existing flow as the fulfillment flow",
                fulfillment_flow_attachment_requested=True,
            )
        )


def test_catalog_candidate_carries_variable_sets_and_groups_end_to_end() -> None:
    provider = RecordingImplementationProvider(
        {
            "changes": [
                {
                    "table": "sc_cat_item",
                    "operation": "insert",
                    "fields": {"name": "Request Temporary Visitor Badge"},
                    "sys_id": None,
                    "rationale": "Create the catalog item.",
                }
            ],
            "test_plan": ["Preview the retrieved Update Set."],
            "rollback_notes": ["Back out the retrieved Update Set."],
        }
    )
    bundle = _catalog_context_bundle()
    story = _catalog_story()
    story = story.model_copy(
        update={
            "description": story.description.replace(
                "Forbidden behavior:",
                "Variable sets: Common Visitor Questions\n"
                "Variable groups: Visitor|visitor_name, business_justification\n"
                "Forbidden behavior:",
            )
        }
    )
    packet = build_implementation_packet(
        story=story,
        policy=_catalog_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
        discovery_context=bundle.table_context,
        surface_context_bundle=bundle,
    )

    candidate = generate_implementation_update_set_candidate_from_packet(
        packet=packet,
        policy=_catalog_policy(),
        provider=provider,
    )

    sc_cat_item_change = next(
        change for change in candidate.changes if change.table == "sc_cat_item"
    )
    assert sc_cat_item_change.fields["variable_sets"] == ["Common Visitor Questions"]
    assert sc_cat_item_change.fields["variable_groups"] == [
        {"title": "Visitor", "variables": ["visitor_name", "business_justification"]}
    ]


def test_form_section_remove_candidate_uses_model_output_and_routes_manual() -> None:
    provider = RecordingImplementationProvider(
        {
            "changes": [
                {
                    "table": "sys_ui_section",
                    "operation": "delete",
                    "fields": {
                        "table": "dmn_demand",
                        "sections": ["Assessment Data", "Financials"],
                        "view": "Default view",
                    },
                    "rationale": "Remove the requested Demand form sections.",
                }
            ],
            "test_plan": ["Preview Demand default view and confirm the tabs are gone."],
            "rollback_notes": ["Restore the removed Demand form sections."],
        }
    )
    bundle = _form_section_context_bundle()
    packet = build_implementation_packet(
        story=_form_section_story(),
        policy=AllowlistPolicy(
            story_types={StoryType.DICTIONARY_FORM},
            tables={"sys_ui_section"},
            operations={"delete"},
            max_points=3,
        ),
        provider_policy=_provider_policy(),
        rags=_rags(),
        discovery_context=bundle.table_context,
        surface_context_bundle=bundle,
    )

    candidate = generate_implementation_update_set_candidate_from_packet(
        packet=packet,
        policy=AllowlistPolicy(
            story_types={StoryType.DICTIONARY_FORM},
            tables={"sys_ui_section"},
            operations={"delete"},
            max_points=3,
        ),
        provider=provider,
    )

    assert provider.payloads
    assert packet.surface_operation_plan is not None
    assert packet.surface_operation_plan["surface"] == "form_layout"
    assert packet.surface_operation_plan["operations"][0]["kind"] == (
        "form_layout.section.remove"
    )
    assert packet.surface_operation_plan["operations"][0]["status"] == "supported"
    assert candidate.status is CandidateStatus.MANUAL_BUILD
    assert candidate.eligibility_decision == "manual_review"
    assert "builder maturity below automated handoff threshold: sys_ui_section=0.30" in (
        candidate.eligibility_reasons
    )
    assert candidate.confidence == 0.3
    assert candidate.changes[0].table == "sys_ui_section"
    assert candidate.changes[0].operation == "delete"
    assert candidate.changes[0].fields == {
        "table": "dmn_demand",
        "sections": ["Assessment Data", "Financials"],
        "view": "Default view",
    }


def test_unsupported_form_layout_surface_operation_routes_to_manual_review() -> None:
    bundle = _form_section_context_bundle()
    story = _form_section_story().model_copy(
        update={
            "number": "STRY0010099",
            "short_description": "DMND: Rename Demand form tab",
            "description": (
                "Target artifact type: Form Section\n"
                "Target table: dmn_demand\n"
                "View: Default view\n"
                "Sections: Financials\n"
                "Actions: Rename the Financials tab to Budget Details."
            ),
            "acceptance_criteria": "The Demand form shows Budget Details instead of Financials.",
        }
    )

    packet = build_implementation_packet(
        story=story,
        policy=AllowlistPolicy(
            story_types={StoryType.DICTIONARY_FORM},
            tables={"sys_ui_section"},
            operations={"delete"},
            max_points=3,
        ),
        provider_policy=_provider_policy(),
        rags=_rags(),
        discovery_context=bundle.table_context,
        surface_context_bundle=bundle,
    )
    candidate = generate_implementation_update_set_candidate_from_packet(
        packet=packet,
        policy=AllowlistPolicy(
            story_types={StoryType.DICTIONARY_FORM},
            tables={"sys_ui_section"},
            operations={"delete"},
            max_points=3,
        ),
        provider=FailingImplementationProvider(),
    )

    assert packet.surface_operation_plan is not None
    assert packet.surface_operation_plan["operations"][0]["kind"] == (
        "form_layout.section.rename"
    )
    assert packet.surface_operation_plan["operations"][0]["status"] == "unsupported"
    assert candidate.status is CandidateStatus.MANUAL_BUILD
    assert candidate.changes == []
    assert "unsupported surface operation: form_layout.section.rename" in (
        candidate.eligibility_reasons
    )


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


def _over_limit_context_bundle() -> ServiceNowSurfaceContextBundle:
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
            for index in range(30)
        ],
        form_sections=[
            DiscoveredFormSection(
                sys_id=f"incident-section-{index}",
                name="incident",
                caption=f"Section {index}",
                elements=[
                    DiscoveredFormElement(
                        sys_id=f"element-{index}-{position}",
                        element=f"field_{position}",
                        position=position,
                    )
                    for position in range(30 if index == 0 else 1)
                ],
            )
            for index in range(5)
        ],
        evidence=["sys_dictionary:incident", "sys_ui_section:incident"],
    )
    return ServiceNowSurfaceContextBundle(
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
                    )
                    for index in range(30)
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
                        name="incident",
                        active=True,
                    )
                ],
                evidence=["sys_ui_section:incident"],
                citations=[
                    {"source": f"sys_ui_section:incident:{index}"} for index in range(30)
                ],
            ),
            ServiceNowSurfaceContext(
                surface="ui_policies",
                source_table="sys_ui_policy",
                required=False,
                records=[
                    ServiceNowSurfaceRecord(
                        source_table="sys_ui_policy",
                        name="not required policy",
                        active=True,
                    )
                ],
                evidence=["sys_ui_policy:incident"],
            ),
        ],
        evidence=["sys_dictionary:incident", "sys_ui_section:incident"],
    )


def _incident_field_story() -> Story:
    return _story().model_copy(
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
    )


def test_model_payload_reports_elisions_when_context_is_truncated() -> None:
    bundle = _over_limit_context_bundle()

    packet = build_implementation_packet(
        story=_incident_field_story(),
        policy=_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
        discovery_context=bundle.table_context,
        surface_context_bundle=bundle,
    )

    payload = packet.to_model_payload()
    model_bundle = payload["instance_context_bundle"]

    assert model_bundle["elisions"] == [
        {
            "content": "surfaces",
            "shown": 2,
            "total": 3,
            "elided": 1,
            "elided_items": ["ui_policies"],
        }
    ]
    assert model_bundle["surfaces"][0]["elisions"] == [
        {"content": "records", "shown": 25, "total": 30, "elided": 5}
    ]
    assert model_bundle["surfaces"][1]["elisions"] == [
        {"content": "citations", "shown": 25, "total": 30, "elided": 5}
    ]
    assert len(model_bundle["surfaces"][1]["citations"]) == 25
    assert model_bundle["table_context"]["elisions"] == [
        {"content": "fields", "shown": 25, "total": 30, "elided": 5},
        {
            "content": "form_sections",
            "shown": 3,
            "total": 5,
            "elided": 2,
            "elided_items": ["Section 3", "Section 4"],
        },
    ]
    assert model_bundle["table_context"]["form_sections"][0]["elisions"] == [
        {"content": "elements", "shown": 25, "total": 30, "elided": 5}
    ]
    summary = payload["controls"]["model_context_elisions"]
    assert [entry["location"] for entry in summary] == [
        "instance_context_bundle.surfaces",
        "instance_context_bundle.table_context.fields",
        "instance_context_bundle.table_context.form_sections",
        "instance_context_bundle.table_context.form_sections[Section 0].elements",
        "instance_context_bundle.surfaces[table_schema].records",
        "instance_context_bundle.surfaces[form_layout].citations",
    ]
    assert {
        "location": "instance_context_bundle.surfaces[table_schema].records",
        "shown": 25,
        "total": 30,
        "elided": 5,
    } in summary
    assert payload["context_dossier"]["model_context_elisions"] == summary
    assert packet.context_dossier["model_context_elisions"] == summary


def test_model_payload_has_no_elision_metadata_when_context_fits_limits() -> None:
    bundle = _ui_policy_context_bundle()

    packet = build_implementation_packet(
        story=_ui_policy_story(),
        policy=_ui_policy_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
        discovery_context=bundle.table_context,
        surface_context_bundle=bundle,
    )

    payload = packet.to_model_payload()

    assert "model_context_elisions" not in payload["controls"]
    assert "model_context_elisions" not in payload["context_dossier"]
    assert "elisions" not in payload["instance_context_bundle"]
    assert all(
        "elisions" not in surface for surface in payload["instance_context_bundle"]["surfaces"]
    )
    assert "elisions" not in str(payload)
    assert "elisions" not in packet.model_dump_json()


def test_model_payload_reports_instance_context_elisions_without_bundle() -> None:
    discovery = _discovery_context().model_copy(
        update={
            "fields": [
                DiscoveredField(
                    element=f"u_field_{index}",
                    column_label=f"Field {index}",
                    internal_type="string",
                )
                for index in range(30)
            ]
        }
    )

    packet = build_implementation_packet(
        story=_story(),
        policy=_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
        discovery_context=discovery,
    )

    payload = packet.to_model_payload()

    assert payload["instance_context"]["elisions"] == [
        {"content": "fields", "shown": 25, "total": 30, "elided": 5}
    ]
    assert len(payload["instance_context"]["fields"]) == 25
    assert payload["controls"]["model_context_elisions"] == [
        {"location": "instance_context.fields", "shown": 25, "total": 30, "elided": 5}
    ]
    assert packet.context_dossier["model_context_elisions"] == [
        {"location": "instance_context.fields", "shown": 25, "total": 30, "elided": 5}
    ]


def test_builder_maturity_context_without_provider_keeps_baseline_entries() -> None:
    bundle = _form_section_context_bundle()

    packet = build_implementation_packet(
        story=_form_section_story(),
        policy=_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
        discovery_context=bundle.table_context,
        surface_context_bundle=bundle,
    )

    notes = "Builder maturity adjusts confidence and routing; it does not suppress reasoning."
    assert packet.context_dossier["builder_maturity"] == [
        {"surface": "form_sections", "score": 0.30, "notes": notes},
        {"surface": "form_layout", "score": 0.95, "notes": notes},
    ]


def test_builder_maturity_context_marks_evidence_adjusted_scores() -> None:
    bundle = _form_section_context_bundle()
    maturity_provider = StubMaturityProvider(
        {
            "form_sections": MaturityEvidence(
                surface="form_sections",
                samples=20,
                successes=18,
                failures=2,
            )
        }
    )

    packet = build_implementation_packet(
        story=_form_section_story(),
        policy=_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
        discovery_context=bundle.table_context,
        surface_context_bundle=bundle,
        maturity_provider=maturity_provider,
    )

    entries = packet.context_dossier["builder_maturity"]
    adjusted = entries[0]
    baseline = entries[1]
    assert adjusted["surface"] == "form_sections"
    assert adjusted["score_source"] == "evidence_adjusted"
    assert adjusted["evidence_samples"] == 20
    assert math.isclose(adjusted["score"], 0.5 * 0.30 + 0.5 * 0.9)
    assert baseline["surface"] == "form_layout"
    assert baseline["score_source"] == "baseline"
    assert baseline["score"] == 0.95
    assert "evidence_samples" not in baseline


def test_evidence_regression_demotes_routing_below_handoff_threshold() -> None:
    packet = build_implementation_packet(
        story=_story(),
        policy=_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
        discovery_context=_discovery_context(),
    )
    regression_evidence = {
        surface: MaturityEvidence(surface=surface, samples=20, successes=4, failures=16)
        for surface in ["table_schema", "form_layout"]
    }

    baseline_candidate = generate_implementation_update_set_candidate_from_packet(
        packet=packet,
        policy=_policy(),
        provider=RecordingImplementationProvider(),
    )
    demoted_candidate = generate_implementation_update_set_candidate_from_packet(
        packet=packet,
        policy=_policy(),
        provider=RecordingImplementationProvider(),
        maturity_provider=StubMaturityProvider(regression_evidence),
    )

    assert baseline_candidate.status is CandidateStatus.READY_FOR_REVIEW
    assert baseline_candidate.eligibility_decision == "eligible"
    assert demoted_candidate.status is CandidateStatus.MANUAL_BUILD
    assert demoted_candidate.eligibility_decision == "manual_review"
    assert math.isclose(demoted_candidate.confidence, 0.5 * 0.95 + 0.5 * 0.2)
    assert any(
        reason.startswith("builder maturity below automated handoff threshold: sys_dictionary=")
        for reason in demoted_candidate.eligibility_reasons
    )
    assert (
        "Builder maturity is evidence-adjusted from baseline 0.95 using 20 recorded "
        "fulfillment outcomes."
    ) in demoted_candidate.reviewer_notes


def test_evidence_promotes_catalog_routing_to_automated_handoff() -> None:
    catalog_response: dict[str, object] = {
        "changes": [
            {
                "table": "sc_cat_item",
                "operation": "insert",
                "fields": {"name": "Request Temporary Visitor Badge"},
                "sys_id": None,
                "rationale": "Create the catalog item.",
            }
        ],
        "test_plan": ["Preview the retrieved Update Set."],
        "rollback_notes": ["Back out the retrieved Update Set."],
    }
    bundle = _catalog_context_bundle()
    packet = build_implementation_packet(
        story=_catalog_story(),
        policy=_catalog_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
        discovery_context=bundle.table_context,
        surface_context_bundle=bundle,
    )
    earned_evidence = {
        surface: MaturityEvidence(surface=surface, samples=60, successes=57, failures=3)
        for surface in [
            "catalog_definitions",
            "catalog_categories",
            "employee_center_topics",
            "employee_center_connected_content",
        ]
    }

    baseline_candidate = generate_implementation_update_set_candidate_from_packet(
        packet=packet,
        policy=_catalog_policy(),
        provider=RecordingImplementationProvider(catalog_response),
    )
    promoted_candidate = generate_implementation_update_set_candidate_from_packet(
        packet=packet,
        policy=_catalog_policy(),
        provider=RecordingImplementationProvider(catalog_response),
        maturity_provider=StubMaturityProvider(earned_evidence),
    )

    assert baseline_candidate.status is CandidateStatus.MANUAL_BUILD
    assert baseline_candidate.eligibility_decision == "manual_review"
    assert any(
        reason.startswith("builder maturity below automated handoff threshold:")
        for reason in baseline_candidate.eligibility_reasons
    )
    assert promoted_candidate.status is CandidateStatus.READY_FOR_REVIEW
    assert promoted_candidate.eligibility_decision == "eligible"
    assert promoted_candidate.confidence == 0.75
    assert (
        "Builder maturity is evidence-adjusted from baseline 0.60 using 60 recorded "
        "fulfillment outcomes."
    ) in promoted_candidate.reviewer_notes


def test_catalog_candidate_with_fulfillment_flow_routes_to_manual_review() -> None:
    catalog_response: dict[str, object] = {
        "changes": [
            {
                "table": "sc_cat_item",
                "operation": "insert",
                "fields": {"name": "Request Temporary Visitor Badge"},
                "sys_id": None,
                "rationale": "Create the catalog item.",
            }
        ],
        "test_plan": ["Preview the retrieved Update Set."],
        "rollback_notes": ["Back out the retrieved Update Set."],
    }
    bundle = _catalog_context_bundle()
    story = _catalog_story()
    story = story.model_copy(
        update={
            "description": story.description.replace(
                "Forbidden behavior:",
                "Fulfillment flow: Attach the existing flow Badge Access Fulfillment "
                "as the fulfillment flow\n"
                "Forbidden behavior:",
            )
        }
    )
    packet = build_implementation_packet(
        story=story,
        policy=_catalog_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
        discovery_context=bundle.table_context,
        surface_context_bundle=bundle,
    )
    earned_catalog_evidence = {
        surface: MaturityEvidence(surface=surface, samples=60, successes=57, failures=3)
        for surface in [
            "catalog_definitions",
            "catalog_categories",
            "employee_center_topics",
            "employee_center_connected_content",
        ]
    }

    candidate = generate_implementation_update_set_candidate_from_packet(
        packet=packet,
        policy=_catalog_policy(),
        provider=RecordingImplementationProvider(catalog_response),
        maturity_provider=StubMaturityProvider(earned_catalog_evidence),
    )

    assert packet.safety_decision == "automated_build"
    sc_cat_item_change = next(
        change for change in candidate.changes if change.table == "sc_cat_item"
    )
    assert sc_cat_item_change.fields["fulfillment_flow"] == "Badge Access Fulfillment"
    # The flow reference rides on sc_cat_item; no extra change tables appear.
    assert {change.table for change in candidate.changes} == {
        "sc_cat_item",
        "item_option_new",
        "sc_cat_item_category",
        "m2m_connected_content",
    }
    # Even with earned catalog-surface evidence, the UAT-unconfirmed
    # fulfillment-flow surface keeps the candidate in manual review.
    assert candidate.status is CandidateStatus.MANUAL_BUILD
    assert candidate.eligibility_decision == "manual_review"
    assert any(
        reason.startswith("builder maturity below automated handoff threshold:")
        and reason.endswith("=0.30")
        for reason in candidate.eligibility_reasons
    )


def _catalog_behavior_intent_overrides() -> dict[str, object]:
    return {
        "catalog_ui_policies": [
            {
                "title": "Show schedule",
                "condition": "visitor_name=external",
                "reverse_if_false": True,
                "actions": [
                    {"variable": "start_date", "visible": "true", "mandatory": "true"},
                    {"variable": "end_date", "visible": "true"},
                ],
            }
        ],
        "catalog_client_scripts": [
            {
                "name": "populate_visitor",
                "script_type": "onLoad",
                "variable": "",
                "actions": [
                    {"kind": "set_value", "variable": "visitor_name", "value": "New visitor"}
                ],
            },
            {
                "name": "clear_end",
                "script_type": "onChange",
                "variable": "start_date",
                "actions": [{"kind": "clear_value", "variable": "end_date"}],
            },
        ],
    }


def test_catalog_changes_render_variable_behavior_from_normalized_intent() -> None:
    changes = _catalog_item_changes_from_normalized_intent(
        _catalog_normalized_intent(**_catalog_behavior_intent_overrides())
    )

    policy_changes = [change for change in changes if change["table"] == "catalog_ui_policy"]
    action_changes = [
        change for change in changes if change["table"] == "catalog_ui_policy_action"
    ]
    script_changes = [change for change in changes if change["table"] == "catalog_script_client"]
    assert len(policy_changes) == 1
    assert policy_changes[0]["fields"] == {
        "short_description": "Show schedule",
        "catalog_item": "Request Temporary Badge",
        "catalog_conditions": "visitor_name=external",
        "reverse_if_false": True,
        "on_load": True,
        "order": 100,
    }
    assert [change["fields"]["variable"] for change in action_changes] == [
        "start_date",
        "end_date",
    ]
    assert action_changes[0]["fields"]["ui_policy"] == "Show schedule"
    assert action_changes[0]["fields"]["mandatory"] == "true"
    assert action_changes[1]["fields"]["mandatory"] == "ignore"
    assert [change["fields"]["name"] for change in script_changes] == [
        "populate_visitor",
        "clear_end",
    ]
    assert script_changes[0]["fields"]["script"] == (
        "function onLoad() {\n"
        "    g_form.setValue('visitor_name', 'New visitor');\n"
        "}"
    )
    assert script_changes[0]["fields"]["fields_written"] == ["visitor_name"]
    assert script_changes[1]["fields"]["field"] == "start_date"
    assert script_changes[1]["fields"]["script"] == (
        "function onChange(control, oldValue, newValue, isLoading, isTemplate) {\n"
        "    if (isLoading) {\n"
        "        return;\n"
        "    }\n"
        "    g_form.clearValue('end_date');\n"
        "}"
    )


def test_catalog_changes_without_variable_behavior_stay_unchanged() -> None:
    changes = _catalog_item_changes_from_normalized_intent(_catalog_normalized_intent())

    assert {change["table"] for change in changes} == {
        "sc_cat_item",
        "item_option_new",
        "sc_cat_item_category",
        "m2m_connected_content",
    }


def test_catalog_changes_reject_rule_on_unknown_variable() -> None:
    with pytest.raises(ModelResponseError, match="references unknown variable: badge_color"):
        _catalog_item_changes_from_normalized_intent(
            _catalog_normalized_intent(
                catalog_ui_policies=[
                    {
                        "title": "Show badge color",
                        "condition": "visitor_name=external",
                        "actions": [{"variable": "badge_color", "visible": "true"}],
                    }
                ]
            )
        )


def test_catalog_changes_reject_rule_with_non_declarative_condition() -> None:
    with pytest.raises(ModelResponseError, match="condition rejected"):
        _catalog_item_changes_from_normalized_intent(
            _catalog_normalized_intent(
                catalog_ui_policies=[
                    {
                        "title": "Show schedule",
                        "condition": "javascript:gs.getUser()",
                        "actions": [{"variable": "start_date", "visible": "true"}],
                    }
                ]
            )
        )


def test_catalog_changes_reject_rule_without_actions_or_invalid_tristate() -> None:
    with pytest.raises(ModelResponseError, match="requires actions"):
        _catalog_item_changes_from_normalized_intent(
            _catalog_normalized_intent(
                catalog_ui_policies=[
                    {"title": "Show schedule", "condition": "visitor_name=external"}
                ]
            )
        )
    with pytest.raises(ModelResponseError, match="must be true, false, or ignore"):
        _catalog_item_changes_from_normalized_intent(
            _catalog_normalized_intent(
                catalog_ui_policies=[
                    {
                        "title": "Show schedule",
                        "condition": "visitor_name=external",
                        "actions": [{"variable": "start_date", "visible": "sometimes"}],
                    }
                ]
            )
        )


def test_catalog_changes_reject_script_on_unknown_variable() -> None:
    with pytest.raises(ModelResponseError, match="references unknown variable: badge_color"):
        _catalog_item_changes_from_normalized_intent(
            _catalog_normalized_intent(
                catalog_client_scripts=[
                    {
                        "name": "populate_color",
                        "script_type": "onLoad",
                        "actions": [
                            {"kind": "set_value", "variable": "badge_color", "value": "blue"}
                        ],
                    }
                ]
            )
        )


def test_catalog_changes_reject_script_with_invalid_action_or_type() -> None:
    with pytest.raises(ModelResponseError, match="action rejected"):
        _catalog_item_changes_from_normalized_intent(
            _catalog_normalized_intent(
                catalog_client_scripts=[
                    {
                        "name": "populate_visitor",
                        "script_type": "onLoad",
                        "actions": [
                            {"kind": "run_script", "variable": "visitor_name", "value": "x"}
                        ],
                    }
                ]
            )
        )
    with pytest.raises(ModelResponseError, match="rejected"):
        _catalog_item_changes_from_normalized_intent(
            _catalog_normalized_intent(
                catalog_client_scripts=[
                    {
                        "name": "populate_visitor",
                        "script_type": "onCellEdit",
                        "actions": [
                            {"kind": "set_value", "variable": "visitor_name", "value": "x"}
                        ],
                    }
                ]
            )
        )


def test_catalog_changes_reject_script_value_with_forbidden_token() -> None:
    with pytest.raises(ModelResponseError, match="rejected"):
        _catalog_item_changes_from_normalized_intent(
            _catalog_normalized_intent(
                catalog_client_scripts=[
                    {
                        "name": "populate_visitor",
                        "script_type": "onLoad",
                        "actions": [
                            {
                                "kind": "set_value",
                                "variable": "visitor_name",
                                "value": "see https://example.com",
                            }
                        ],
                    }
                ]
            )
        )


def _catalog_behavior_policy() -> AllowlistPolicy:
    return AllowlistPolicy(
        story_types={StoryType.DICTIONARY_FORM},
        tables={
            "sc_cat_item",
            "item_option_new",
            "sc_cat_item_category",
            "m2m_connected_content",
            "catalog_ui_policy",
            "catalog_ui_policy_action",
            "catalog_script_client",
        },
        operations={"insert", "update"},
        max_points=3,
    )


def test_catalog_candidate_with_variable_behavior_routes_to_manual_review() -> None:
    provider = RecordingImplementationProvider(
        {
            "changes": [
                {
                    "table": "sc_cat_item",
                    "operation": "insert",
                    "fields": {"name": "Request Temporary Visitor Badge"},
                    "sys_id": None,
                    "rationale": "Create the catalog item.",
                }
            ],
            "test_plan": ["Preview the retrieved Update Set."],
            "rollback_notes": ["Back out the retrieved Update Set."],
        }
    )
    bundle = _catalog_context_bundle()
    story = _catalog_story()
    story = story.model_copy(
        update={
            "description": story.description.replace(
                "Forbidden behavior:",
                "Variable rules: Require sponsor|visitor_name=external|"
                "require=sponsor|show=sponsor\n"
                "Variable scripts: populate_visitor|onload|set=visitor_name=New visitor\n"
                "Forbidden behavior:",
            )
        }
    )
    packet = build_implementation_packet(
        story=story,
        policy=_catalog_behavior_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
        discovery_context=bundle.table_context,
        surface_context_bundle=bundle,
    )

    candidate = generate_implementation_update_set_candidate_from_packet(
        packet=packet,
        policy=_catalog_behavior_policy(),
        provider=provider,
    )

    assert packet.safety_decision == "automated_build"
    assert {change.table for change in candidate.changes} == {
        "sc_cat_item",
        "item_option_new",
        "sc_cat_item_category",
        "m2m_connected_content",
        "catalog_ui_policy",
        "catalog_ui_policy_action",
        "catalog_script_client",
    }
    script_change = next(
        change for change in candidate.changes if change.table == "catalog_script_client"
    )
    assert "g_form.setValue('visitor_name', 'New visitor');" in str(
        script_change.fields["script"]
    )
    # The new behavior surfaces start below the automated handoff threshold by
    # design, so the candidate is preserved for manual review.
    assert candidate.status is CandidateStatus.MANUAL_BUILD
    assert candidate.eligibility_decision == "manual_review"
    assert any(
        reason.startswith("builder maturity below automated handoff threshold:")
        and "=0.30" in reason
        for reason in candidate.eligibility_reasons
    )


def test_catalog_variable_rule_intent_parser_fails_closed_on_malformed_shapes() -> None:
    cases: list[tuple[object, str]] = [
        ("not-a-list", "catalog variable rules must be a list"),
        (["not-an-object"], "catalog variable rule intent must be an object"),
        ([{"condition": "visitor_name=external"}], "catalog variable rule intent missing title"),
        ([{"title": "Show schedule"}], "catalog variable rule Show schedule missing condition"),
        (
            [
                {
                    "title": "Show schedule",
                    "condition": "visitor_name=external",
                    "actions": ["not-an-object"],
                }
            ],
            "action must be an object",
        ),
        (
            [
                {
                    "title": "Show schedule",
                    "condition": "visitor_name=external",
                    "actions": [{"visible": "true"}],
                }
            ],
            "action missing variable",
        ),
    ]
    for raw_rules, message in cases:
        with pytest.raises(ModelResponseError, match=message):
            _catalog_item_changes_from_normalized_intent(
                _catalog_normalized_intent(catalog_ui_policies=raw_rules)
            )


def test_catalog_client_script_intent_parser_fails_closed_on_malformed_shapes() -> None:
    cases: list[tuple[object, str]] = [
        ("not-a-list", "catalog client scripts must be a list"),
        (["not-an-object"], "catalog client script intent must be an object"),
        ([{"script_type": "onLoad"}], "catalog client script intent missing name"),
        (
            [{"name": "populate_visitor"}],
            "catalog client script populate_visitor missing script type",
        ),
        (
            [{"name": "populate_visitor", "script_type": "onLoad", "actions": []}],
            "catalog client script populate_visitor requires actions",
        ),
        (
            [
                {
                    "name": "populate_visitor",
                    "script_type": "onLoad",
                    "actions": ["not-an-object"],
                }
            ],
            "action must be an object",
        ),
    ]
    for raw_scripts, message in cases:
        with pytest.raises(ModelResponseError, match=message):
            _catalog_item_changes_from_normalized_intent(
                _catalog_normalized_intent(catalog_client_scripts=raw_scripts)
            )


def _record_producer_policy() -> AllowlistPolicy:
    return AllowlistPolicy(
        story_types={StoryType.DICTIONARY_FORM},
        tables={"sc_cat_item_producer", "item_option_new", "sc_cat_item_category"},
        operations={"insert", "update"},
        max_points=3,
    )


def _record_producer_story() -> Story:
    return Story(
        sys_id="record-producer-story-sys-id",
        number="STRY0010140",
        short_description="JEDI UAT: Report Security Incident record producer",
        description=(
            "Target artifact type: Record Producer\n"
            "Artifact name: Report Security Incident\n"
            "Short description: Report a security incident for triage.\n"
            "Target table: incident\n"
            "Catalog: Service Catalog\n"
            "Category: Services\n"
            "Variables: summary|Summary|single_line_text|map=short_description|"
            "mandatory=true|order=100; "
            "caller|Caller|reference|sys_user|active=true|map=caller_id|order=200\n"
            "Forbidden behavior: Do not create producer scripts, flows, approvals, "
            "user criteria, or integrations."
        ),
        acceptance_criteria="Delivery is a retrieved Update Set ready for preview and commit.",
        story_points=3,
        priority=4,
        state="Work in Progress",
        data_classification=DataClassification.PUBLIC,
    )


def _record_producer_context_bundle() -> ServiceNowSurfaceContextBundle:
    table_context = InstanceDiscoveryContext(
        target_table="incident",
        table_label="Incident",
        table_exists=True,
        supports_custom_fields=True,
        fields=[
            DiscoveredField(
                element="short_description",
                column_label="Short description",
                internal_type="string",
            ),
            DiscoveredField(
                element="caller_id",
                column_label="Caller",
                internal_type="reference",
            ),
        ],
        form_sections=[],
        evidence=["sys_db_object:incident", "sys_dictionary:incident"],
    )
    return ServiceNowSurfaceContextBundle(
        target_table="incident",
        required_surfaces=["table_schema", "catalog_definitions", "catalog_categories"],
        table_context=table_context,
        surfaces=[
            ServiceNowSurfaceContext(
                surface="table_schema",
                source_table="sys_dictionary",
                required=True,
                records=[
                    ServiceNowSurfaceRecord(
                        source_table="sys_dictionary",
                        name="short_description",
                        active=True,
                        summary="Short description",
                        metadata={"internal_type": "string"},
                    ),
                    ServiceNowSurfaceRecord(
                        source_table="sys_dictionary",
                        name="caller_id",
                        active=True,
                        summary="Caller",
                        metadata={"internal_type": "reference"},
                    ),
                ],
                evidence=["sys_dictionary:incident"],
                confidence=1.0,
            ),
            ServiceNowSurfaceContext(
                surface="catalog_definitions",
                source_table="sc_catalog",
                required=True,
                records=[
                    ServiceNowSurfaceRecord(
                        source_table="sc_catalog",
                        name="Service Catalog",
                        active=True,
                    )
                ],
                evidence=["sc_catalog:active"],
                confidence=0.95,
            ),
            ServiceNowSurfaceContext(
                surface="catalog_categories",
                source_table="sc_category",
                required=True,
                records=[
                    ServiceNowSurfaceRecord(
                        source_table="sc_category",
                        name="Services",
                        active=True,
                    )
                ],
                evidence=["sc_category:active"],
                confidence=0.95,
            ),
        ],
        evidence=["sys_dictionary:incident", "sc_catalog:active", "sc_category:active"],
    )


def test_record_producer_candidate_reconciles_changes_from_normalized_intent() -> None:
    provider = RecordingImplementationProvider(
        {
            "changes": [
                {
                    "table": "sc_cat_item_producer",
                    "operation": "insert",
                    "fields": {"name": "Report Security Incident"},
                    "sys_id": None,
                    "rationale": "Create the record producer.",
                }
            ],
            "test_plan": ["Preview the retrieved Update Set."],
            "rollback_notes": ["Back out the retrieved Update Set."],
        }
    )
    bundle = _record_producer_context_bundle()
    packet = build_implementation_packet(
        story=_record_producer_story(),
        policy=_record_producer_policy(),
        provider_policy=_provider_policy(),
        rags=_rags(),
        discovery_context=bundle.table_context,
        surface_context_bundle=bundle,
    )

    candidate = generate_implementation_update_set_candidate_from_packet(
        packet=packet,
        policy=_record_producer_policy(),
        provider=provider,
    )

    assert {change.table for change in candidate.changes} == {
        "sc_cat_item_producer",
        "item_option_new",
        "sc_cat_item_category",
    }
    producer_change = next(
        change for change in candidate.changes if change.table == "sc_cat_item_producer"
    )
    assert producer_change.fields["table_name"] == "incident"
    assert "script" not in producer_change.fields
    variable_changes = [
        change for change in candidate.changes if change.table == "item_option_new"
    ]
    assert [change.fields["field"] for change in variable_changes] == [
        "short_description",
        "caller_id",
    ]
    assert all(change.fields["map_to_field"] is True for change in variable_changes)
    assert variable_changes[1].fields["reference"] == "sys_user"
    assert variable_changes[1].fields["reference_qualifier"] == "active=true"
    # The record producer builder is below the automated handoff maturity
    # threshold (0.30), so the candidate routes to manual review by design.
    assert candidate.eligibility_decision == "manual_review"
    assert candidate.status is CandidateStatus.MANUAL_BUILD
    assert any(
        "builder maturity below automated handoff threshold" in reason
        and "0.30" in reason
        for reason in candidate.eligibility_reasons
    )


def _record_producer_normalized_intent(**overrides: object) -> dict[str, object]:
    producer: dict[str, object] = {
        "name": "Report Security Incident",
        "short_description": "Report a security incident for triage.",
        "target_table": "incident",
        "catalog": "Service Catalog",
        "category": "Services",
        "variables": [
            {
                "name": "summary",
                "label": "Summary",
                "type": "single_line_text",
                "field": "short_description",
            },
            {
                "name": "caller",
                "label": "Caller",
                "type": "reference",
                "reference_table": "sys_user",
                "reference_qualifier": "active=true",
                "field": "caller_id",
            },
        ],
    }
    producer.update(overrides)
    return {"record_producer": producer}


def test_record_producer_changes_reject_producer_script() -> None:
    intent = _record_producer_normalized_intent()
    intent["record_producer_script"] = "current.short_description = producer.summary;"

    with pytest.raises(ModelResponseError, match="must not carry a producer script"):
        _record_producer_changes_from_normalized_intent(intent)


def test_record_producer_changes_require_normalized_record_producer_intent() -> None:
    with pytest.raises(ModelResponseError, match="requires normalized record producer intent"):
        _record_producer_changes_from_normalized_intent({"artifact_name": "Producer"})


def test_record_producer_changes_require_field_mapping_on_every_variable() -> None:
    with pytest.raises(ModelResponseError, match="requires a target field mapping"):
        _record_producer_changes_from_normalized_intent(
            _record_producer_normalized_intent(
                variables=[
                    {"name": "summary", "label": "Summary", "type": "single_line_text"}
                ]
            )
        )


def test_record_producer_changes_reject_duplicate_field_mappings() -> None:
    with pytest.raises(ModelResponseError, match="more than once"):
        _record_producer_changes_from_normalized_intent(
            _record_producer_normalized_intent(
                variables=[
                    {
                        "name": "summary",
                        "label": "Summary",
                        "type": "single_line_text",
                        "field": "short_description",
                    },
                    {
                        "name": "details",
                        "label": "Details",
                        "type": "multi_line_text",
                        "field": "short_description",
                    },
                ]
            )
        )


def test_record_producer_changes_reject_non_declarative_reference_qualifier() -> None:
    with pytest.raises(ModelResponseError, match="reference qualifier rejected"):
        _record_producer_changes_from_normalized_intent(
            _record_producer_normalized_intent(
                variables=[
                    {
                        "name": "caller",
                        "label": "Caller",
                        "type": "reference",
                        "reference_table": "sys_user",
                        "reference_qualifier": "javascript:gs.getUser()",
                        "field": "caller_id",
                    }
                ]
            )
        )
