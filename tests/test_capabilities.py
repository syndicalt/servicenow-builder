from jedi_devproject.capabilities import (
    Capability,
    CapabilityProfile,
    FieldFormIntent,
    StoryCapabilityAssessment,
    SuitabilityOutcome,
    capability_profile,
    generation_capability_profiles,
)


def test_field_form_intent_derives_custom_field_name_from_label() -> None:
    intent = FieldFormIntent(
        target_table="incident",
        field_label="Antics",
        field_type="string",
        max_length=4000,
        placement_anchor="description",
        placement_position="below",
    )

    assert intent.field_name == "u_antics"


def test_assessment_for_supported_dictionary_form_is_automated() -> None:
    assessment = StoryCapabilityAssessment(
        story_number="STRY0010001",
        outcome=SuitabilityOutcome.AUTOMATED_BUILD,
        capabilities={
            Capability.DICTIONARY_FIELD_CREATE,
            Capability.FIELD_LABEL_CREATE,
            Capability.FORM_LAYOUT_PLACE_FIELD,
        },
        supported_capabilities={
            Capability.DICTIONARY_FIELD_CREATE,
            Capability.FIELD_LABEL_CREATE,
            Capability.FORM_LAYOUT_PLACE_FIELD,
        },
        intent=FieldFormIntent(
            target_table="incident",
            field_label="Antics",
            field_type="string",
            max_length=4000,
            placement_anchor="description",
            placement_position="below",
        ),
        reasons=["supported low-complexity dictionary/form request"],
        missing_details=[],
        unsupported_capabilities=set(),
        risk_score=0.18,
        confidence=0.82,
    )

    assert assessment.is_automated
    assert assessment.intent is not None
    assert assessment.intent.field_name == "u_antics"
    assert assessment.unsupported_capabilities == set()


def test_assessment_reports_unsupported_capability() -> None:
    assessment = StoryCapabilityAssessment(
        story_number="STRY0099999",
        outcome=SuitabilityOutcome.UNSUPPORTED_CAPABILITY,
        capabilities={Capability.FLOW_MODIFY},
        supported_capabilities={Capability.DICTIONARY_FIELD_CREATE},
        intent=None,
        reasons=["Flow Designer changes are not supported by this pipeline"],
        missing_details=[],
        unsupported_capabilities={Capability.FLOW_MODIFY},
        risk_score=0.65,
        confidence=0.7,
    )

    assert not assessment.is_automated
    assert assessment.unsupported_capability_names == ["flow_modify"]


def test_code_surface_analysis_profiles_are_context_only() -> None:
    expected = {
        Capability.BUSINESS_RULE_ANALYZE: (["table_schema", "business_rules"], "sys_script"),
        Capability.CLIENT_SCRIPT_ANALYZE: (["table_schema", "client_scripts"], "sys_script_client"),
        Capability.SCRIPT_INCLUDE_ANALYZE: (["script_includes"], "sys_script_include"),
    }

    for capability, (required_context, artifact_table) in expected.items():
        profile = capability_profile(capability)

        assert isinstance(profile, CapabilityProfile)
        assert profile.capability is capability
        assert profile.status == "context_only"
        assert profile.required_instance_context == required_context
        assert artifact_table in profile.supported_artifacts
        assert "generation" in " ".join(profile.unsupported_cases)
        assert profile.creates_update_set is False


def test_capability_profiles_record_current_and_target_story_point_maturity() -> None:
    dictionary_profile = capability_profile(Capability.DICTIONARY_FIELD_CREATE)
    business_rule_profile = capability_profile(Capability.BUSINESS_RULE_GENERATE)

    assert dictionary_profile.current_max_story_points == 5
    assert dictionary_profile.target_max_story_points == 5
    assert dictionary_profile.researcher == "dictionary_form_researcher"
    assert dictionary_profile.build_pipeline == "dictionary_form_update_set_pipeline"
    assert dictionary_profile.creates_update_set is True

    assert business_rule_profile.status == "designed"
    assert business_rule_profile.current_max_story_points == 0
    assert business_rule_profile.target_max_story_points == 5
    assert business_rule_profile.researcher == "code_surface_researcher"
    assert business_rule_profile.build_pipeline == "business_rule_update_set_pipeline"
    assert business_rule_profile.creates_update_set is True


def test_generation_registry_names_every_handled_surface_pipeline() -> None:
    profiles = generation_capability_profiles()

    assert [profile.capability for profile in profiles] == [
        Capability.DICTIONARY_FIELD_CREATE,
        Capability.FORM_LAYOUT_PLACE_FIELD,
        Capability.BUSINESS_RULE_GENERATE,
        Capability.CLIENT_SCRIPT_GENERATE,
        Capability.SCRIPT_INCLUDE_GENERATE,
    ]
    assert all(profile.target_max_story_points == 5 for profile in profiles)
    assert all(profile.researcher for profile in profiles)
    assert all(profile.build_pipeline for profile in profiles)
