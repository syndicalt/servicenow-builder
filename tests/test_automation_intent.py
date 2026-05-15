from jedi_devproject.automation_intent import (
    AutomationIntentSource,
    AutomationIntentType,
    extract_automation_intent,
)
from jedi_devproject.capabilities import Capability
from jedi_devproject.models import DataClassification, Story


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
