from jedi_devproject.automation_intent import (
    AutomationIntentSource,
    AutomationIntentType,
    extract_automation_intent,
)
from jedi_devproject.capabilities import Capability
from jedi_devproject.models import DataClassification, Story
from jedi_devproject.story_features import explicit_reference_qualifier


def _story(
    *,
    number: str,
    short_description: str,
    description: str,
    acceptance_criteria: str = "Delivery is a retrieved Update Set.",
    story_points: float = 3,
) -> Story:
    return Story(
        sys_id="story-sys-id",
        number=number,
        short_description=short_description,
        description=description,
        acceptance_criteria=acceptance_criteria,
        story_points=story_points,
        priority=4,
        state="Ready",
        data_classification=DataClassification.PUBLIC,
    )


def test_extracts_structured_client_script_intent_without_cmdb_discovery_work() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010022",
            short_description="JEDI UAT: Warn when Software Incident has no CI",
            description=(
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
                "Reverse behavior: Not applicable\n"
                "Forbidden behavior: Do not use GlideAjax, document APIs, window "
                "APIs, browser storage, external calls, credentials, form submit, "
                "or unrelated field writes.\n"
                "Rollback expectation: Deactivate or delete the generated Client "
                "Script through the retrieved Update Set review process."
            ),
        )
    )

    assert intent.source is AutomationIntentSource.STRUCTURED
    assert intent.intent_type is AutomationIntentType.CLIENT_SCRIPT
    assert intent.capability is Capability.CLIENT_SCRIPT_GENERATE
    assert intent.target_table == "incident"
    assert intent.artifact_name == "JEDI UAT Software CI Reminder"
    assert intent.client_script_type == "onchange"
    assert intent.target_field == "category"
    assert intent.fields_read == ["category", "cmdb_ci"]
    assert intent.fields_written == []
    assert intent.fields_affected == []
    assert intent.required_instance_context == ["table_schema", "client_scripts"]
    assert "cmdb_discovery_maps" not in intent.required_instance_context
    assert intent.missing_details == []


def test_extracts_structured_ui_policy_intent_without_forbidden_capability_bleed() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010024",
            short_description="JEDI UAT: Require Assignment group for Software Incidents",
            description=(
                "Target artifact type: UI Policy\n"
                "Target table: incident\n"
                "Artifact name: JEDI UAT Software Assignment Required\n"
                "Condition: category is software\n"
                "Actions: Make assignment_group mandatory and visible.\n"
                "Fields read: category\n"
                "Fields written / affected: assignment_group\n"
                "Reverse behavior: Reverse if false is enabled.\n"
                "Reverse if false: true\n"
                "Run scripts: false\n"
                "Forbidden behavior: Do not use Client Script, Business Rule, "
                "Script Include, Flow, ACL, integration calls, credentials, or "
                "cross-table behavior."
            ),
        )
    )

    assert intent.source is AutomationIntentSource.STRUCTURED
    assert intent.intent_type is AutomationIntentType.UI_POLICY
    assert intent.capability is Capability.UI_POLICY_GENERATE
    assert intent.target_table == "incident"
    assert intent.fields_read == ["category"]
    assert intent.fields_affected == ["assignment_group"]
    assert intent.reverse_if_false is True
    assert intent.run_scripts is False
    assert intent.required_instance_context == ["table_schema", "form_layout", "ui_policies"]
    assert intent.missing_details == []


def test_structured_intent_reports_missing_required_fields_without_legacy_guessing() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010999",
            short_description="JEDI UAT: Incomplete Client Script",
            description=(
                "Target artifact type: Client Script\n"
                "Target table: incident\n"
                "Client script type: onChange\n"
                "Condition: category changes to software\n"
                "Fields written / affected: none"
            ),
        )
    )

    assert intent.source is AutomationIntentSource.STRUCTURED
    assert intent.capability is Capability.CLIENT_SCRIPT_GENERATE
    assert intent.missing_details == ["target field", "expected behavior", "fields read"]


def test_extracts_structured_business_rule_intent() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010021",
            short_description="JEDI UAT: Default inquiry short description",
            description=(
                "Target artifact type: Business Rule\n"
                "Target table: incident\n"
                "Artifact name: JEDI UAT Default Inquiry Short Description\n"
                "Trigger timing: before\n"
                "Trigger operations: insert, update\n"
                "Condition: category is inquiry and short_description is empty\n"
                "Expected behavior: set short_description to Inquiry needs triage\n"
                "Fields read: category, short_description\n"
                "Fields written: short_description"
            ),
        )
    )

    assert intent.intent_type is AutomationIntentType.BUSINESS_RULE
    assert intent.capability is Capability.BUSINESS_RULE_GENERATE
    assert intent.trigger_timing == "before"
    assert intent.trigger_operations == ["insert", "update"]
    assert intent.fields_written == ["short_description"]
    assert intent.required_instance_context == ["table_schema", "business_rules"]
    assert intent.missing_details == []


def test_extracts_business_rule_intent_with_timing_alias_and_combined_fields_written() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010021",
            short_description="JEDI UAT: Default inquiry Incident short description",
            description=(
                "Target artifact type: Business Rule\n"
                "Target table: incident\n"
                "Artifact name: JEDI UAT Default Inquiry Short Description\n"
                "Timing: before\n"
                "Trigger operations: insert and update\n"
                "Condition: category is inquiry and short_description is empty\n"
                "Actions: Set short_description to Inquiry needs triage.\n"
                "Fields read: category, short_description\n"
                "Fields written / affected: short_description\n"
                "Reverse behavior: Not applicable\n"
                "Forbidden behavior: Do not use GlideRecord, outbound calls, credentials, "
                "async Business Rules, display Business Rules, delete rules, globals, "
                "or cross-table writes."
            ),
        )
    )

    assert intent.intent_type is AutomationIntentType.BUSINESS_RULE
    assert intent.capability is Capability.BUSINESS_RULE_GENERATE
    assert intent.target_table == "incident"
    assert intent.artifact_name == "JEDI UAT Default Inquiry Short Description"
    assert intent.trigger_timing == "before"
    assert intent.trigger_operations == ["insert", "update"]
    assert intent.fields_read == ["category", "short_description"]
    assert intent.fields_written == ["short_description"]
    assert intent.fields_affected == ["short_description"]
    assert intent.required_instance_context == ["table_schema", "business_rules"]
    assert intent.missing_details == []


def test_extracts_structured_script_include_intent() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010023",
            short_description="JEDI UAT: Add string utility",
            description=(
                "Target artifact type: Script Include\n"
                "Artifact name: JediUatStringUtil\n"
                "Scope: global\n"
                "Client callable: false\n"
                "Expected server-side behavior: provide normalizeText(value)\n"
                "Tables read: none\n"
                "Tables written: none\n"
                "Fields read: none\n"
                "Fields written: none"
            ),
        )
    )

    assert intent.intent_type is AutomationIntentType.SCRIPT_INCLUDE
    assert intent.capability is Capability.SCRIPT_INCLUDE_GENERATE
    assert intent.target_table is None
    assert intent.script_include_scope == "global"
    assert intent.client_callable is False
    assert intent.required_instance_context == ["script_includes"]
    assert intent.missing_details == []


def test_extracts_script_include_intent_with_combined_fields_written_line() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010023",
            short_description="JEDI UAT: Add Incident text normalization Script Include",
            description=(
                "Target artifact type: Script Include\n"
                "Target table: global\n"
                "Artifact name: JediUatIncidentTextUtils\n"
                "API name: global.JediUatIncidentTextUtils\n"
                "Scope: global\n"
                "Client callable: false\n"
                "Public methods: normalizeText(value)\n"
                "Expected server-side behavior: normalizeText returns an empty string "
                "for null or undefined input and returns the trimmed string value for "
                "other input.\n"
                "Tables read: none\n"
                "Tables written: none\n"
                "Fields read: none\n"
                "Fields written / affected: none\n"
                "Reverse behavior: Not applicable\n"
                "Forbidden behavior: Do not use GlideRecord, outbound calls, credentials, "
                "security changes, caller creation, or client callable behavior.\n"
                "Rollback expectation: Delete the generated Script Include through the "
                "retrieved Update Set review process."
            ),
        )
    )

    assert intent.intent_type is AutomationIntentType.SCRIPT_INCLUDE
    assert intent.capability is Capability.SCRIPT_INCLUDE_GENERATE
    assert intent.artifact_name == "JediUatIncidentTextUtils"
    assert intent.target_table == "global"
    assert intent.script_include_scope == "global"
    assert intent.client_callable is False
    assert intent.tables_read == []
    assert intent.tables_written == []
    assert intent.fields_read == []
    assert intent.fields_written == []
    assert intent.required_instance_context == ["script_includes"]
    assert intent.missing_details == []


def test_extracts_structured_dictionary_form_intent() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010100",
            short_description="JEDI UAT: Add review source",
            description=(
                "Target artifact type: Dictionary Form\n"
                "Target table: incident\n"
                "Field label: Review Source\n"
                "Field name: u_review_source\n"
                "Field type: string\n"
                "Max length: 120\n"
                "Placement: below description"
            ),
        )
    )

    assert intent.intent_type is AutomationIntentType.DICTIONARY_FORM
    assert intent.capability is Capability.DICTIONARY_FIELD_CREATE
    assert intent.field_label == "Review Source"
    assert intent.field_name == "u_review_source"
    assert intent.max_length == 120
    assert intent.placement_anchor == "description"
    assert intent.placement_position == "below"
    assert intent.required_instance_context == ["table_schema", "form_layout"]
    assert intent.missing_details == []


def test_extracts_dictionary_field_and_form_placement_intent() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010020",
            short_description="JEDI UAT: Add vendor reference to Problem form",
            description=(
                "Target artifact type: Dictionary field and form placement\n"
                "Target table: problem\n"
                "Field name: u_vendor_reference\n"
                "Field label: Vendor Reference\n"
                "Field type: reference\n"
                "Reference table: core_company\n"
                "Reference qualifier: vendor=true\n"
                "Form view: Default view\n"
                "Placement anchor: Description\n"
                "Placement position: after Description\n"
                "Actions: Create the field and place it on the default Problem form.\n"
                "Fields read: description\n"
                "Fields written / affected: u_vendor_reference\n"
                "Reverse behavior: Not applicable\n"
                "Forbidden behavior: Do not create ACLs, flows, Business Rules, "
                "Client Scripts, data migration, integrations, or cross-table automation.\n"
                "Rollback expectation: Remove the dictionary field and the form "
                "layout element through the retrieved Update Set review process."
            ),
        )
    )

    assert intent.intent_type is AutomationIntentType.DICTIONARY_FORM
    assert intent.capability is Capability.DICTIONARY_FIELD_CREATE
    assert intent.target_table == "problem"
    assert intent.field_name == "u_vendor_reference"
    assert intent.field_label == "Vendor Reference"
    assert intent.field_type == "reference"
    assert intent.reference_table == "core_company"
    assert intent.reference_qualifier == "vendor=true"
    assert intent.placement_anchor == "description"
    assert intent.placement_position == "below"
    assert intent.required_instance_context == ["table_schema", "form_layout"]
    assert intent.missing_details == []


def test_extracts_structured_form_section_removal_intent() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010011",
            short_description="DMND: Hide Demand form tabs",
            description=(
                "Target artifact type: Form Section Removal\n"
                "Target table: dmn_demand\n"
                "View: Default view\n"
                "Sections: Assessment, Financials\n"
                "Actions: Remove the Assessment and Financials tabs from the "
                "default Demand form layout.\n"
                "Forbidden behavior: Do not create UI Policies, Client Scripts, "
                "Business Rules, ACLs, or Flow changes."
            ),
        )
    )

    assert intent.source is AutomationIntentSource.STRUCTURED
    assert intent.intent_type is AutomationIntentType.FORM_SECTION
    assert intent.capability is Capability.FORM_SECTION_REMOVE
    assert intent.target_table == "dmn_demand"
    assert intent.form_view == "Default view"
    assert intent.form_sections == ["Assessment", "Financials"]
    assert intent.required_instance_context == ["form_sections", "form_layout"]
    assert intent.missing_details == []


def test_extracts_generic_form_section_intent_only_when_action_is_removal() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010011",
            short_description="DMND: Hide Demand form tabs",
            description=(
                "Target artifact type: Form Section\n"
                "Target table: dmn_demand\n"
                "View: Default view\n"
                "Sections: Assessment, Financials\n"
                "Actions: Hide the Assessment and Financials tabs."
            ),
        )
    )

    assert intent.intent_type is AutomationIntentType.FORM_SECTION
    assert intent.capability is Capability.FORM_SECTION_REMOVE
    assert intent.form_sections == ["Assessment", "Financials"]


def test_rejects_generic_form_section_intent_without_removal_action() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010099",
            short_description="DMND: Rename Demand form tab",
            description=(
                "Target artifact type: Form Section\n"
                "Target table: dmn_demand\n"
                "View: Default view\n"
                "Sections: Financials\n"
                "Actions: Rename the Financials tab to Budget Details."
            ),
        )
    )

    assert intent.intent_type is AutomationIntentType.FORM_SECTION
    assert intent.capability is Capability.UNKNOWN
    assert intent.form_sections == ["Financials"]
    assert intent.missing_details == []


def test_extracts_structured_catalog_item_intent_with_variables_and_topic() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010101",
            short_description="JEDI UAT: Add temporary badge catalog item",
            description=(
                "Target artifact type: Catalog Item\n"
                "Artifact name: Request Temporary Badge\n"
                "Short description: Request a temporary access badge for a visitor.\n"
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
        )
    )

    assert intent.source is AutomationIntentSource.STRUCTURED
    assert intent.intent_type is AutomationIntentType.CATALOG_ITEM
    assert intent.capability is Capability.CATALOG_ITEM_CREATE
    assert intent.artifact_name == "Request Temporary Badge"
    assert intent.catalog_item_short_description == (
        "Request a temporary access badge for a visitor."
    )
    assert intent.catalog_name == "Service Catalog"
    assert intent.category_name == "Services"
    assert intent.taxonomy_name == "Employee"
    assert intent.employee_center_topic == "Technology services / Software / Access issues"
    assert intent.catalog_variables == [
        {
            "name": "visitor_name",
            "label": "Visitor name",
            "type": "single_line_text",
            "mandatory": True,
            "order": 100,
        },
        {
            "name": "business_justification",
            "label": "Business justification",
            "type": "multi_line_text",
            "mandatory": True,
            "order": 200,
        },
        {
            "name": "sponsor",
            "label": "Sponsor",
            "type": "reference",
            "reference_table": "sys_user",
            "reference_qualifier": "active=true",
            "mandatory": True,
            "order": 300,
        },
    ]
    assert intent.required_instance_context == [
        "catalog_definitions",
        "catalog_categories",
        "employee_center_topics",
        "employee_center_connected_content",
    ]
    assert intent.missing_details == []


def _catalog_story_description(*extra_lines: str) -> str:
    return (
        "Target artifact type: Catalog Item\n"
        "Artifact name: Request Temporary Badge\n"
        "Short description: Request a temporary access badge for a visitor.\n"
        "Catalog: Service Catalog\n"
        "Category: Services\n"
        "Taxonomy: Employee\n"
        "Employee Center topic: Technology services / Software / Access issues\n"
        "Variables: visitor_name|Visitor name|single_line_text|mandatory=true|order=100; "
        "start_date|Start date|date|order=200; "
        "end_date|End date|date|order=300\n" + "".join(f"{line}\n" for line in extra_lines)
    )


def test_extracts_catalog_variable_sets_and_groups_as_typed_intent() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010110",
            short_description="JEDI UAT: Badge item with shared sets and grouping",
            description=_catalog_story_description(
                "Variable sets: ; Common Visitor Questions; Network Access; "
                "common visitor questions",
                "Variable groups: ;Schedule|start_date, end_date",
            ),
        )
    )

    assert intent.catalog_variable_sets == ["Common Visitor Questions", "Network Access"]
    assert [group.model_dump() for group in intent.catalog_variable_groups] == [
        {"title": "Schedule", "variables": ["start_date", "end_date"]}
    ]
    assert intent.catalog_variable_set_creation is False
    assert intent.missing_details == []


def test_catalog_variable_set_creation_request_sets_flag_without_inventing_names() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010111",
            short_description="JEDI UAT: Badge item with new variable set",
            description=_catalog_story_description(
                "Variable sets: Create a new Visitor Details set",
            ),
        )
    )

    assert intent.catalog_variable_sets == []
    assert intent.catalog_variable_set_creation is True
    assert intent.missing_details == []


def test_malformed_catalog_variable_groups_surface_as_missing_detail() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010112",
            short_description="JEDI UAT: Badge item with malformed group",
            description=_catalog_story_description("Variable groups: Schedule"),
        )
    )

    assert intent.catalog_variable_groups == []
    assert intent.missing_details == ["variable groups"]


def test_catalog_variable_group_with_undeclared_member_is_a_missing_detail() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010113",
            short_description="JEDI UAT: Badge item group references unknown variable",
            description=_catalog_story_description("Variable groups: Schedule|badge_color"),
        )
    )

    assert intent.missing_details == ["variable group members"]


def test_explicit_attach_existing_fulfillment_flow_extracts_flow_name() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010140",
            short_description="JEDI UAT: Badge item attaching an existing flow",
            description=_catalog_story_description(
                "Fulfillment flow: Attach the existing flow Badge Access Fulfillment "
                "as the fulfillment flow",
            ),
        )
    )

    assert intent.fulfillment_flow == (
        "Attach the existing flow Badge Access Fulfillment as the fulfillment flow"
    )
    assert intent.fulfillment_flow_name == "Badge Access Fulfillment"
    assert intent.fulfillment_flow_attachment_requested is True
    assert intent.missing_details == []


def test_explicit_attach_existing_fulfillment_flow_supports_quoted_names() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010141",
            short_description="JEDI UAT: Badge item attaching a quoted flow",
            description=_catalog_story_description(
                'Fulfillment flow: attach the existing flow "Badge Access Fulfillment" '
                "as the fulfillment flow.",
            ),
        )
    )

    assert intent.fulfillment_flow_name == "Badge Access Fulfillment"
    assert intent.fulfillment_flow_attachment_requested is True
    assert intent.missing_details == []


def test_attach_fulfillment_flow_request_without_a_name_is_a_missing_detail() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010142",
            short_description="JEDI UAT: Badge item attaching an unnamed flow",
            description=_catalog_story_description(
                "Fulfillment flow: Attach an existing flow as the fulfillment flow",
            ),
        )
    )

    assert intent.fulfillment_flow_name is None
    assert intent.fulfillment_flow_attachment_requested is True
    assert intent.missing_details == ["fulfillment flow name"]


def test_fulfillment_flow_creation_request_is_carried_without_attachment() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010143",
            short_description="JEDI UAT: Badge item creating a flow",
            description=_catalog_story_description(
                "Fulfillment flow: Create a new Badge Fulfillment flow",
            ),
        )
    )

    assert intent.fulfillment_flow == "Create a new Badge Fulfillment flow"
    assert intent.fulfillment_flow_name is None
    assert intent.fulfillment_flow_attachment_requested is False
    assert intent.missing_details == []


def test_ambiguous_fulfillment_flow_phrasing_is_carried_without_attachment() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010144",
            short_description="JEDI UAT: Badge item with ambiguous flow phrasing",
            description=_catalog_story_description(
                "Fulfillment flow: Badge Access Fulfillment",
            ),
        )
    )

    assert intent.fulfillment_flow == "Badge Access Fulfillment"
    assert intent.fulfillment_flow_name is None
    assert intent.fulfillment_flow_attachment_requested is False


def test_modify_fulfillment_flow_request_is_carried_without_attachment() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010145",
            short_description="JEDI UAT: Badge item modifying a flow",
            description=_catalog_story_description(
                "Fulfillment flow: Attach the existing flow Badge Access Fulfillment "
                "as the fulfillment flow and modify its approval step",
            ),
        )
    )

    assert intent.fulfillment_flow_name is None
    assert intent.fulfillment_flow_attachment_requested is False


def test_catalog_reference_variable_carries_explicit_qualifier_phrase() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010114",
            short_description="JEDI UAT: Badge item with filtered reference variable",
            description=_catalog_story_description().replace(
                "end_date|End date|date|order=300",
                "assignment_group|Assignment group|reference|sys_user_group|"
                "filtered to active groups|order=300",
            ),
        )
    )

    assert intent.catalog_variables[2] == {
        "name": "assignment_group",
        "label": "Assignment group",
        "type": "reference",
        "reference_table": "sys_user_group",
        "reference_qualifier": "active=true",
        "mandatory": False,
        "order": 300,
    }


def test_catalog_reference_variable_omits_ambiguous_qualifier_prose() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010115",
            short_description="JEDI UAT: Badge item with ambiguous filter prose",
            description=_catalog_story_description().replace(
                "end_date|End date|date|order=300",
                "assignment_group|Assignment group|reference|sys_user_group|"
                "filtered to groups my manager owns|order=300",
            ),
        )
    )

    assert "reference_qualifier" not in intent.catalog_variables[2]


def test_catalog_reference_variable_carries_scripted_qualifier_for_rejection() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010116",
            short_description="JEDI UAT: Badge item with scripted qualifier",
            description=_catalog_story_description().replace(
                "end_date|End date|date|order=300",
                "assignment_group|Assignment group|reference|sys_user_group|"
                "javascript:gs.getUser()|order=300",
            ),
        )
    )

    assert intent.catalog_variables[2]["reference_qualifier"] == "javascript:gs.getUser()"


def test_explicit_reference_qualifier_maps_only_unambiguous_phrases() -> None:
    assert explicit_reference_qualifier("") is None
    assert explicit_reference_qualifier("active=true") == "active=true"
    assert explicit_reference_qualifier("filtered to active=true") == "active=true"
    assert (
        explicit_reference_qualifier("where active=true^type=catalog")
        == "active=true^type=catalog"
    )
    assert explicit_reference_qualifier("filtered to active groups") == "active=true"
    assert explicit_reference_qualifier("limited to only active users.") == "active=true"
    assert explicit_reference_qualifier("filtered to groups my manager owns") is None
    assert explicit_reference_qualifier("popular groups") is None


def test_catalog_item_intent_requires_variables_and_topic() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010102",
            short_description="JEDI UAT: Incomplete catalog item",
            description=(
                "Target artifact type: Catalog Item\n"
                "Artifact name: Request Temporary Badge\n"
                "Short description: Request a temporary access badge.\n"
                "Catalog: Service Catalog\n"
                "Category: Services\n"
                "Taxonomy: Employee"
            ),
        )
    )

    assert intent.intent_type is AutomationIntentType.CATALOG_ITEM
    assert intent.capability is Capability.CATALOG_ITEM_CREATE
    assert intent.missing_details == ["Employee Center topic", "variables"]


def test_unknown_or_unsupported_structured_intents_are_typed_without_context() -> None:
    unknown = extract_automation_intent(
        _story(
            number="STRY0010998",
            short_description="Unknown artifact",
            description="Target artifact type: Portal Widget\nTarget table: sp_widget",
        )
    )
    acl = extract_automation_intent(
        _story(
            number="STRY0010997",
            short_description="ACL artifact",
            description="Target artifact type: ACL\nTarget table: incident",
        )
    )

    assert unknown.intent_type is AutomationIntentType.UNKNOWN
    assert unknown.capability is Capability.UNKNOWN
    assert unknown.required_instance_context == []
    assert acl.intent_type is AutomationIntentType.ACL
    assert acl.capability is Capability.ACL_MODIFY
    assert acl.required_instance_context == []


def test_extracts_catalog_variable_rules_and_scripts_as_typed_intent() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010120",
            short_description="JEDI UAT: Badge item with variable behavior",
            description=_catalog_story_description(
                "Variable rules: Show schedule|visitor_name=external|"
                "show=start_date,end_date|require=start_date|reverse=true",
                "Variable scripts: populate_visitor|onload|set=visitor_name=New visitor; "
                "clear_end|onchange|start_date|clear=end_date",
            ),
        )
    )

    assert [rule.model_dump() for rule in intent.catalog_ui_policies] == [
        {
            "title": "Show schedule",
            "condition": "visitor_name=external",
            "reverse_if_false": True,
            "actions": [
                {
                    "variable": "start_date",
                    "visible": "true",
                    "mandatory": "true",
                    "disabled": "ignore",
                    "cleared": False,
                },
                {
                    "variable": "end_date",
                    "visible": "true",
                    "mandatory": "ignore",
                    "disabled": "ignore",
                    "cleared": False,
                },
            ],
        }
    ]
    assert [spec.model_dump() for spec in intent.catalog_client_scripts] == [
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
            "actions": [{"kind": "clear_value", "variable": "end_date", "value": ""}],
        },
    ]
    assert intent.missing_details == []


def test_malformed_catalog_variable_rules_surface_as_missing_detail() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010121",
            short_description="JEDI UAT: Badge item with malformed rule",
            description=_catalog_story_description("Variable rules: Show schedule"),
        )
    )

    assert intent.catalog_ui_policies == []
    assert "variable rules" in intent.missing_details


def test_catalog_variable_rule_with_conflicting_effects_is_a_missing_detail() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010122",
            short_description="JEDI UAT: Badge item with conflicting rule",
            description=_catalog_story_description(
                "Variable rules: Show schedule|visitor_name=external|"
                "show=start_date|hide=start_date",
            ),
        )
    )

    assert intent.catalog_ui_policies == []
    assert "variable rules" in intent.missing_details


def test_catalog_variable_rule_with_undeclared_member_is_a_missing_detail() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010123",
            short_description="JEDI UAT: Badge item rule on unknown variable",
            description=_catalog_story_description(
                "Variable rules: Show badge color|visitor_name=external|show=badge_color",
            ),
        )
    )

    assert intent.missing_details == ["variable rule members"]


def test_malformed_catalog_variable_scripts_surface_as_missing_detail() -> None:
    malformed = extract_automation_intent(
        _story(
            number="STRY0010124",
            short_description="JEDI UAT: Badge item with malformed script",
            description=_catalog_story_description("Variable scripts: populate_visitor|onload"),
        )
    )
    free_form = extract_automation_intent(
        _story(
            number="STRY0010125",
            short_description="JEDI UAT: Badge item with free-form script",
            description=_catalog_story_description(
                "Variable scripts: populate_visitor|onload|script=g_form.setValue('x','y')",
            ),
        )
    )

    assert malformed.catalog_client_scripts == []
    assert "variable scripts" in malformed.missing_details
    assert free_form.catalog_client_scripts == []
    assert "variable scripts" in free_form.missing_details


def test_catalog_variable_script_with_undeclared_member_is_a_missing_detail() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010126",
            short_description="JEDI UAT: Badge item script on unknown variable",
            description=_catalog_story_description(
                "Variable scripts: populate_color|onload|set=badge_color=blue",
            ),
        )
    )

    assert intent.missing_details == ["variable script members"]


def test_standalone_catalog_ui_policy_intent_is_typed_for_manual_routing() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010127",
            short_description="JEDI UAT: Hide a variable on an existing item",
            description=(
                "Target artifact type: Catalog UI Policy\n"
                "Artifact name: Hide schedule on existing badge item\n"
                "Condition: needs_schedule=no"
            ),
        )
    )

    assert intent.source is AutomationIntentSource.STRUCTURED
    assert intent.intent_type is AutomationIntentType.CATALOG_UI_POLICY
    assert intent.capability is Capability.CATALOG_UI_POLICY_GENERATE


def test_standalone_catalog_client_script_intent_is_typed_for_manual_routing() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010128",
            short_description="JEDI UAT: Populate a variable on an existing item",
            description=(
                "Target artifact type: Catalog Client Script\n"
                "Artifact name: Populate description on existing badge item"
            ),
        )
    )

    assert intent.source is AutomationIntentSource.STRUCTURED
    assert intent.intent_type is AutomationIntentType.CATALOG_CLIENT_SCRIPT
    assert intent.capability is Capability.CATALOG_CLIENT_SCRIPT_GENERATE


def test_catalog_variable_rule_parser_skips_empty_entries_but_keeps_valid_rules() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010140",
            short_description="JEDI UAT: Badge item rule with stray separator",
            description=_catalog_story_description(
                "Variable rules: ; Show schedule|visitor_name=external|show=start_date|"
                "reverse=false;",
            ),
        )
    )

    assert len(intent.catalog_ui_policies) == 1
    assert intent.catalog_ui_policies[0].reverse_if_false is False


def test_catalog_variable_rule_parser_discards_all_rules_on_any_malformed_entry() -> None:
    malformed_rule_lines = [
        # Empty title.
        "Variable rules: |visitor_name=external|show=start_date",
        # Duplicate titles.
        "Variable rules: Show schedule|visitor_name=external|show=start_date; "
        "show schedule|visitor_name=internal|hide=start_date",
        # Part without a value.
        "Variable rules: Show schedule|visitor_name=external|show",
        # Unparseable reverse decision.
        "Variable rules: Show schedule|visitor_name=external|show=start_date|reverse=maybe",
        # Unknown effect key.
        "Variable rules: Show schedule|visitor_name=external|run_script=start_date",
        # Empty member list.
        "Variable rules: Show schedule|visitor_name=external|show=,",
        # Only a reverse part, no effects.
        "Variable rules: Show schedule|visitor_name=external|reverse=true",
    ]
    for line in malformed_rule_lines:
        intent = extract_automation_intent(
            _story(
                number="STRY0010141",
                short_description="JEDI UAT: Badge item with malformed rule entry",
                description=_catalog_story_description(line),
            )
        )
        assert intent.catalog_ui_policies == [], line
        assert "variable rules" in intent.missing_details, line


def test_catalog_variable_script_parser_skips_empty_entries_but_keeps_valid_scripts() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010142",
            short_description="JEDI UAT: Badge item script with stray separator",
            description=_catalog_story_description(
                "Variable scripts: ; populate_visitor|onload|set=visitor_name=New visitor;",
            ),
        )
    )

    assert len(intent.catalog_client_scripts) == 1


def test_catalog_variable_script_parser_discards_all_scripts_on_any_malformed_entry() -> None:
    malformed_script_lines = [
        # Unsupported script type.
        "Variable scripts: populate_visitor|onCellEdit|set=visitor_name=x",
        # Duplicate script names.
        "Variable scripts: populate_visitor|onload|set=visitor_name=x; "
        "populate_visitor|onload|set=visitor_name=y",
        # onChange watched variable is not a plain name.
        "Variable scripts: clear_end|onchange|set=end_date=x|clear=end_date",
        # onChange with no actions after the watched variable.
        "Variable scripts: clear_end|onchange|start_date",
        # Action part without a value.
        "Variable scripts: populate_visitor|onload|set",
        # set action without a variable name.
        "Variable scripts: populate_visitor|onload|set==x",
        # set action without a value.
        "Variable scripts: populate_visitor|onload|set=visitor_name=",
        # clear action with an empty member.
        "Variable scripts: clear_end|onchange|start_date|clear=---",
    ]
    for line in malformed_script_lines:
        intent = extract_automation_intent(
            _story(
                number="STRY0010143",
                short_description="JEDI UAT: Badge item with malformed script entry",
                description=_catalog_story_description(line),
            )
        )
        assert intent.catalog_client_scripts == [], line
        assert "variable scripts" in intent.missing_details, line


def _record_producer_story_description(*extra_lines: str) -> str:
    return (
        "Target artifact type: Record Producer\n"
        "Artifact name: Report Security Incident\n"
        "Short description: Report a security incident for triage.\n"
        "Target table: incident\n"
        "Catalog: Service Catalog\n"
        "Category: Services\n"
        "Variables: summary|Summary|single_line_text|map=short_description|"
        "mandatory=true|order=100; "
        "details|Details|multi_line_text|map=description|order=200; "
        "caller|Caller|reference|sys_user|active=true|map=caller_id|order=300\n"
        + "".join(f"{line}\n" for line in extra_lines)
    )


def test_extracts_structured_record_producer_intent_with_field_mappings() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010130",
            short_description="JEDI UAT: Add security record producer",
            description=_record_producer_story_description(),
        )
    )

    assert intent.source is AutomationIntentSource.STRUCTURED
    assert intent.intent_type is AutomationIntentType.RECORD_PRODUCER
    assert intent.capability is Capability.RECORD_PRODUCER_CREATE
    assert intent.target_table == "incident"
    assert intent.artifact_name == "Report Security Incident"
    assert intent.catalog_name == "Service Catalog"
    assert intent.category_name == "Services"
    assert intent.catalog_variables == [
        {
            "name": "summary",
            "label": "Summary",
            "type": "single_line_text",
            "mandatory": True,
            "order": 100,
            "field": "short_description",
        },
        {
            "name": "details",
            "label": "Details",
            "type": "multi_line_text",
            "mandatory": False,
            "order": 200,
            "field": "description",
        },
        {
            "name": "caller",
            "label": "Caller",
            "type": "reference",
            "reference_table": "sys_user",
            "reference_qualifier": "active=true",
            "mandatory": False,
            "order": 300,
            "field": "caller_id",
        },
    ]
    assert intent.record_producer is not None
    assert intent.record_producer.name == "Report Security Incident"
    assert intent.record_producer.target_table == "incident"
    assert intent.record_producer.variables[0]["field"] == "short_description"
    assert intent.record_producer_script is None
    assert intent.required_instance_context == [
        "table_schema",
        "catalog_definitions",
        "catalog_categories",
    ]
    assert intent.missing_details == []


def test_record_producer_intent_without_field_mappings_is_a_missing_detail() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010131",
            short_description="JEDI UAT: Producer without mappings",
            description=_record_producer_story_description().replace(
                "map=short_description|", ""
            ),
        )
    )

    assert intent.intent_type is AutomationIntentType.RECORD_PRODUCER
    assert intent.missing_details == ["variable field mappings"]
    assert intent.record_producer is None


def test_record_producer_intent_reports_missing_required_fields() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010132",
            short_description="JEDI UAT: Incomplete record producer",
            description=(
                "Target artifact type: Record Producer\n"
                "Artifact name: Report Security Incident"
            ),
        )
    )

    assert intent.intent_type is AutomationIntentType.RECORD_PRODUCER
    assert intent.capability is Capability.RECORD_PRODUCER_CREATE
    assert intent.missing_details == [
        "short description",
        "target table",
        "catalog",
        "category",
        "variables",
    ]
    assert intent.record_producer is None


def test_record_producer_script_request_is_carried_for_rejection() -> None:
    intent = extract_automation_intent(
        _story(
            number="STRY0010133",
            short_description="JEDI UAT: Producer with script mapping",
            description=_record_producer_story_description(
                "Producer script: current.short_description = producer.summary;",
            ),
        )
    )

    assert intent.record_producer_script == (
        "current.short_description = producer.summary;"
    )
    assert intent.missing_details == []
