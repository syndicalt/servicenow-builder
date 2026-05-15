from jedi_devproject.capabilities import Capability, SuitabilityOutcome
from jedi_devproject.capability_analysis import analyze_story_capabilities
from jedi_devproject.models import DataClassification, Story


def _story(
    *,
    short_description: str,
    description: str,
    acceptance_criteria: str,
    number: str = "STRY0010001",
    story_points: float = 2,
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


def test_incident_field_story_is_automated_dictionary_form() -> None:
    assessment = analyze_story_capabilities(
        _story(
            short_description="Add a New Field to the Incident Form",
            description=(
                "As an incident manager, I would like a new field added to the "
                "Incident form.\n\n- Field Name: Antics\n- Field Type: String\n"
                "- Length: 4000"
            ),
            acceptance_criteria=(
                "- A new field labeled Antics exists on the incident form.\n"
                "- The field is placed below the Description field.\n"
                "- All incident users are able to read and write to the Antics field."
            ),
        )
    )

    assert assessment.outcome is SuitabilityOutcome.AUTOMATED_BUILD
    assert assessment.intent is not None
    assert assessment.intent.target_table == "incident"
    assert assessment.intent.field_label == "Antics"
    assert assessment.intent.field_name == "u_antics"
    assert assessment.intent.field_type == "string"
    assert assessment.intent.max_length == 4000
    assert assessment.intent.placement_anchor == "description"
    assert assessment.intent.placement_position == "below"
    assert assessment.capabilities == {
        Capability.DICTIONARY_FIELD_CREATE,
        Capability.FIELD_LABEL_CREATE,
        Capability.FORM_LAYOUT_PLACE_FIELD,
    }


def test_story_field_story_remains_automated_dictionary_form() -> None:
    assessment = analyze_story_capabilities(
        _story(
            number="STRY0010013",
            short_description="Add AI Review Notes field to Story form",
            description=(
                "Add a new custom field to the rm_story table named u_ai_review_notes "
                "and place it on the Story form below Description."
            ),
            acceptance_criteria="The AI Review Notes field stores review notes.",
        )
    )

    assert assessment.outcome is SuitabilityOutcome.AUTOMATED_BUILD
    assert assessment.intent is not None
    assert assessment.intent.target_table == "rm_story"
    assert assessment.intent.field_name == "u_ai_review_notes"


def test_problem_vendor_reference_story_extracts_reference_metadata() -> None:
    assessment = analyze_story_capabilities(
        _story(
            number="STRY0010002",
            short_description="Add Vendor Reference field to Problem form",
            description=(
                "Add a new custom reference field named u_vendor_reference to the "
                "Problem table. The field should reference the core_company table "
                "and only allow companies where vendor=true. Place the field on "
                "the default Problem form below the Description field."
            ),
            acceptance_criteria=(
                "- The field type is Reference.\n"
                "- The field references core_company.\n"
                "- The field uses a reference qualifier of vendor=true."
            ),
            story_points=3,
        )
    )

    assert assessment.outcome is SuitabilityOutcome.AUTOMATED_BUILD
    assert assessment.intent is not None
    assert assessment.intent.target_table == "problem"
    assert assessment.intent.field_label == "Vendor Reference"
    assert assessment.intent.field_name == "u_vendor_reference"
    assert assessment.intent.field_type == "reference"
    assert assessment.intent.reference_table == "core_company"
    assert assessment.intent.reference_qualifier == "vendor=true"
    assert assessment.intent.placement_anchor == "description"


def test_missing_target_table_needs_clarification() -> None:
    assessment = analyze_story_capabilities(
        _story(
            short_description="Add a new field",
            description="Add a string field named Comments below Description.",
            acceptance_criteria="The field is visible on the form.",
        )
    )

    assert assessment.outcome is SuitabilityOutcome.NEEDS_CLARIFICATION
    assert "target table" in assessment.missing_details


def test_acl_requirement_is_unsupported_capability() -> None:
    assessment = analyze_story_capabilities(
        _story(
            short_description="Add restricted Incident field",
            description=(
                "Add a string field named Security Notes to the Incident form and "
                "create an ACL so only admins can write it."
            ),
            acceptance_criteria="Only admins can write Security Notes.",
        )
    )

    assert assessment.outcome is SuitabilityOutcome.UNSUPPORTED_CAPABILITY
    assert Capability.ACL_MODIFY in assessment.unsupported_capabilities


def test_negative_scope_constraints_do_not_count_as_requested_capabilities() -> None:
    assessment = analyze_story_capabilities(
        _story(
            short_description="Add Review Summary field to Change Request form",
            description=(
                "Create a custom string field on table named change_request and place "
                "it on the change_request form. Field label: UAT Review Summary. "
                "Field name: u_uat_review_summary. Field type: string. Max length: "
                "255 characters. Placement: below description on the default form. "
                "Do not create ACLs, flows, data migration, or integrations."
            ),
            acceptance_criteria=(
                "- The change_request table has an active dictionary field named "
                "u_uat_review_summary.\n"
                "- The field appears on the default Change Request form below Description."
            ),
            story_points=3,
        )
    )

    assert assessment.outcome is SuitabilityOutcome.AUTOMATED_BUILD
    assert Capability.ACL_MODIFY not in assessment.capabilities
    assert Capability.FLOW_MODIFY not in assessment.capabilities
    assert Capability.DATA_MIGRATION not in assessment.capabilities
    assert Capability.INTEGRATION_MODIFY not in assessment.capabilities
    assert assessment.unsupported_capabilities == set()


def test_business_rule_negative_safety_constraints_do_not_block_generation() -> None:
    assessment = analyze_story_capabilities(
        _story(
            short_description="Create Incident inquiry short description default Business Rule",
            description=(
                "Create a Business Rule for table named incident. Business Rule name: "
                "JEDI UAT Default Inquiry Short Description. Trigger timing: before. "
                "Trigger operations: insert and update. Condition: when category is "
                "inquiry and short_description is empty. Expected behavior: set "
                "short_description to Inquiry needs triage. Fields read: category, "
                "short_description. Fields written: short_description. Do not use "
                "GlideRecord, outbound calls, credentials, async/display rules, "
                "deletes, or cross-table writes."
            ),
            acceptance_criteria="- The rule runs before insert and update only.",
            story_points=3,
        )
    )

    assert assessment.outcome is SuitabilityOutcome.AUTOMATED_BUILD
    assert assessment.unsupported_capabilities == set()
    assert "business rule generation includes forbidden behavior" not in assessment.reasons


def test_client_script_negative_safety_constraints_do_not_block_generation() -> None:
    assessment = analyze_story_capabilities(
        _story(
            short_description="Create Problem software category onLoad Client Script",
            description=(
                "Create a Client Script for table named problem. Client Script name: "
                "JEDI UAT Software Category Notice. Client script type: onLoad. "
                "Condition: when category is software. Expected behavior: show an "
                "informational form message. Fields read: category. Fields written: "
                "none. Do not use GlideAjax, browser storage, document or window APIs, "
                "external calls, credentials, or DOM manipulation outside g_form APIs."
            ),
            acceptance_criteria="- It uses g_form APIs to show the message.",
            story_points=3,
        )
    )

    assert assessment.outcome is SuitabilityOutcome.AUTOMATED_BUILD
    assert assessment.unsupported_capabilities == set()
    assert "client script generation includes forbidden behavior" not in assessment.reasons


def test_high_point_story_routes_to_manual_developer_build() -> None:
    assessment = analyze_story_capabilities(
        _story(
            short_description="Add incident automation",
            description="Add a field to the Incident form and update assignment workflow.",
            acceptance_criteria="The workflow assigns incidents to the right group.",
            story_points=8,
        )
    )

    assert assessment.outcome is SuitabilityOutcome.MANUAL_DEVELOPER_BUILD
    assert "story points exceed full-maturity max: 8.0 > 5" in assessment.reasons


def test_five_point_dictionary_form_story_routes_to_manual_until_current_maturity_expands() -> None:
    assessment = analyze_story_capabilities(
        _story(
            number="STRY0010115",
            short_description="Add Vendor Reference field to Problem form",
            description=(
                "Add a new custom reference field named u_vendor_reference to the "
                "Problem table. The field should reference the core_company table "
                "and only allow companies where vendor=true. Place the field on "
                "the default Problem form below the Description field."
            ),
            acceptance_criteria=(
                "- The field type is Reference.\n"
                "- The field references core_company.\n"
                "- The field uses a reference qualifier of vendor=true."
            ),
            story_points=5,
        )
    )

    assert assessment.outcome is SuitabilityOutcome.MANUAL_DEVELOPER_BUILD
    assert "story points exceed current automation max: 5.0 > 3" in assessment.reasons


def test_complete_business_rule_story_is_eligible_for_automated_generation() -> None:
    assessment = analyze_story_capabilities(
        _story(
            number="STRY0010116",
            short_description="Create Incident priority note Business Rule",
            description=(
                "Create a before update Business Rule on the Incident table. "
                "Condition: priority changes to 1 - Critical. Expected behavior: "
                "set work_notes to Priority escalated by automation. Fields read: "
                "priority. Fields written: work_notes."
            ),
            acceptance_criteria=(
                "- Updating an Incident priority to 1 - Critical adds the work note.\n"
                "- The rule runs before update only.\n"
                "- Rollback removes the generated Business Rule."
            ),
            story_points=3,
        )
    )

    assert assessment.outcome is SuitabilityOutcome.AUTOMATED_BUILD
    assert Capability.BUSINESS_RULE_GENERATE in assessment.capabilities
    assert Capability.BUSINESS_RULE_ANALYZE not in assessment.capabilities
    assert assessment.target_table == "incident"
    assert assessment.required_instance_context == ["table_schema", "business_rules"]
    assert assessment.reasons == ["supported table-local business rule generation request"]


def test_business_rule_story_routes_to_context_analysis() -> None:
    assessment = analyze_story_capabilities(
        _story(
            number="STRY0010112",
            short_description="Analyze Incident Business Rule for priority stamping",
            description=(
                "Analyze whether the incident table needs a before update Business Rule "
                "to set u_priority_stamp when priority changes."
            ),
            acceptance_criteria=(
                "The automation should inspect existing Incident Business Rules and "
                "report whether generation is supported."
            ),
        )
    )

    assert assessment.outcome is SuitabilityOutcome.CONTEXT_ANALYSIS
    assert Capability.BUSINESS_RULE_ANALYZE in assessment.capabilities
    assert assessment.target_table == "incident"
    assert assessment.required_instance_context == ["table_schema", "business_rules"]
    assert "business rule generation is not enabled yet" in assessment.reasons


def test_business_rule_story_without_target_table_needs_clarification() -> None:
    assessment = analyze_story_capabilities(
        _story(
            short_description="Analyze a Business Rule",
            description="Check whether a before update Business Rule is needed.",
            acceptance_criteria="The analysis names the current rules.",
        )
    )

    assert assessment.outcome is SuitabilityOutcome.NEEDS_CLARIFICATION
    assert "target table" in assessment.missing_details


def test_complete_client_script_story_is_eligible_for_automated_generation() -> None:
    assessment = analyze_story_capabilities(
        _story(
            number="STRY0010118",
            short_description="Create Incident category onChange Client Script",
            description=(
                "Create an onChange Client Script on the Incident table for the "
                "category field. Condition: category changes to software. Expected "
                "behavior: show an info message telling the user to confirm the "
                "configuration item. Fields read: category. Fields written: none. "
                "Messages shown: Confirm the CI before saving."
            ),
            acceptance_criteria=(
                "- Changing Incident category to software shows the message.\n"
                "- The script uses g_form APIs only.\n"
                "- Rollback removes the generated Client Script."
            ),
            story_points=3,
        )
    )

    assert assessment.outcome is SuitabilityOutcome.AUTOMATED_BUILD
    assert Capability.CLIENT_SCRIPT_GENERATE in assessment.capabilities
    assert Capability.CLIENT_SCRIPT_ANALYZE not in assessment.capabilities
    assert assessment.target_table == "incident"
    assert assessment.required_instance_context == ["table_schema", "client_scripts"]
    assert assessment.reasons == ["supported table-local client script generation request"]


def test_client_script_story_routes_to_context_analysis() -> None:
    assessment = analyze_story_capabilities(
        _story(
            number="STRY0010113",
            short_description="Analyze Incident Client Script for category behavior",
            description=(
                "Analyze whether the incident table needs an onChange Client Script "
                "for category behavior."
            ),
            acceptance_criteria="Existing Incident Client Scripts are retrieved.",
        )
    )

    assert assessment.outcome is SuitabilityOutcome.CONTEXT_ANALYSIS
    assert Capability.CLIENT_SCRIPT_ANALYZE in assessment.capabilities
    assert assessment.target_table == "incident"
    assert assessment.required_instance_context == ["table_schema", "client_scripts"]
    assert "client script generation is not enabled yet" in assessment.reasons


def test_script_include_story_routes_to_global_context_analysis() -> None:
    assessment = analyze_story_capabilities(
        _story(
            number="STRY0010114",
            short_description="Analyze AssignmentUtils Script Include",
            description=(
                "Analyze the AssignmentUtils Script Include to determine whether "
                "shared assignment helper logic already exists."
            ),
            acceptance_criteria="Existing Script Includes are retrieved for review.",
        )
    )

    assert assessment.outcome is SuitabilityOutcome.CONTEXT_ANALYSIS
    assert Capability.SCRIPT_INCLUDE_ANALYZE in assessment.capabilities
    assert assessment.target_table == "global"
    assert assessment.required_instance_context == ["script_includes"]
    assert "script include generation is not enabled yet" in assessment.reasons


def test_complete_script_include_story_is_eligible_for_automated_generation() -> None:
    assessment = analyze_story_capabilities(
        _story(
            number="STRY0010120",
            short_description="Create JediIncidentUtils Script Include",
            description=(
                "Create a Script Include named JediIncidentUtils in Global scope. "
                "Client callable: false. Expected server-side behavior: provide a "
                "normalizeCategory(category) function that returns the category "
                "lowercased. Tables read: none. Tables written: none. Fields read: "
                "none. Fields written: none."
            ),
            acceptance_criteria=(
                "- Calling normalizeCategory('Software') returns software.\n"
                "- The Script Include is not client callable.\n"
                "- Rollback removes the generated Script Include."
            ),
            story_points=3,
        )
    )

    assert assessment.outcome is SuitabilityOutcome.AUTOMATED_BUILD
    assert Capability.SCRIPT_INCLUDE_GENERATE in assessment.capabilities
    assert Capability.SCRIPT_INCLUDE_ANALYZE not in assessment.capabilities
    assert assessment.target_table == "global"
    assert assessment.required_instance_context == ["script_includes"]
    assert assessment.reasons == ["supported utility script include generation request"]


def test_script_include_story_with_fields_read_and_performs_is_not_dictionary_form() -> None:
    assessment = analyze_story_capabilities(
        _story(
            number="STRY0010017",
            short_description="UAT: Create global text normalization Script Include",
            description=(
                "Create a Script Include named JediUatStringUtil. Scope: global. "
                "Client callable: false. Expected server-side behavior: expose a "
                "public method normalizeText(value) that returns an empty string when "
                "value is nil and otherwise returns the trimmed lowercase string value. "
                "Tables read: none. Tables written: none. Fields read: none. "
                "Fields written: none. Do not use GlideRecord, outbound calls, "
                "credentials, security changes, or caller creation."
            ),
            acceptance_criteria=(
                "- A global Script Include named JediUatStringUtil is created.\n"
                "- api_name is global.JediUatStringUtil.\n"
                "- It is not client callable.\n"
                "- It exposes normalizeText(value) as a public method.\n"
                "- It performs no table writes and uses no outbound calls.\n"
                "- Delivery is a retrieved Update Set ready for ServiceNow preview and commit."
            ),
            story_points=3,
        )
    )

    assert assessment.outcome is SuitabilityOutcome.AUTOMATED_BUILD
    assert assessment.capabilities == {Capability.SCRIPT_INCLUDE_GENERATE}
    assert assessment.required_instance_context == ["script_includes"]


def test_complete_ui_policy_story_is_eligible_for_automated_generation() -> None:
    assessment = analyze_story_capabilities(
        _story(
            number="STRY0010122",
            short_description="Create Incident assignment group UI Policy",
            description=(
                "Create a UI Policy on the Incident table. Condition: category is "
                "software. Expected behavior: make the assignment_group field "
                "mandatory and visible. Fields read: category. Fields affected: "
                "assignment_group. Reverse if false: true."
            ),
            acceptance_criteria=(
                "- When Incident category is software, Assignment group is mandatory.\n"
                "- When Incident category is not software, the policy reverses.\n"
                "- Rollback removes the generated UI Policy and UI Policy Action."
            ),
            story_points=3,
        )
    )

    assert assessment.outcome is SuitabilityOutcome.AUTOMATED_BUILD
    assert Capability.UI_POLICY_GENERATE in assessment.capabilities
    assert assessment.target_table == "incident"
    assert assessment.intent is None
    assert assessment.required_instance_context == ["table_schema", "form_layout", "ui_policies"]
    assert assessment.reasons == ["supported declarative ui policy generation request"]
