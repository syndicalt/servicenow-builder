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
